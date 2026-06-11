# 資料庫壓測（pgbench）

直接連 PostgreSQL（跳過 nginx / auth / backend），量**資料庫本身**的極限：
TPS、latency、連線數上限、聚合查詢成本。與 `k6/`（測整條 HTTP 鏈）互補。

## 為什麼要單獨測 DB

k6 測的是 nginx→auth/backend→DB 整條鏈，DB 的成本會被 argon2、Python checker 蓋過。
pgbench 隔離出純資料庫層，回答「PostgreSQL 自己能撐多少」。

## 前置

```sh
docker compose up -d db
# 灌假資料（學號 112703101~，共 500 名）
cd backend && set -a && source ../.env && set +a
uv run python ../scripts/seed_load_test_data.py --count 500
```

pgbench 內建於 postgres image，無需安裝。

## 四個查詢（對應系統真實熱點）

| query | 對應系統操作 | 成本 |
|-------|-------------|------|
| `simple` | `GET /api/public/departments`（260 筆） | 最輕，baseline 對照 |
| `student` | check_graduation 撈學生修課（enrollment×course 複合 JOIN） | 輕 |
| `dashboard` | admin dashboard 課程失敗率（全表 GROUP BY + 條件聚合） | **最重** |
| `token` | auth 驗證(SELECT) + 登入發 token(INSERT) | 輕（不含 argon2，argon2 在應用層） |

## 四種模式

| mode | pgbench 參數 | 目的 |
|------|-------------|------|
| `baseline` | `-c 1 -T 20` | 單連線基準，單筆 latency 底線 |
| `load` | `-c 20 -j 4 -T 60` | 穩定並發，穩態 TPS / latency |
| `stress` | `-c 10→30→60→100→150`（階梯，各 30s） | 找 TPS 不再上升、latency 爆炸的拐點 |
| `spike` | `-c 200 -j 8 -T 30` | 瞬間連線暴衝，測連線建立風暴（PG 每連線 fork 一 process） |

## 執行

```sh
./db/loadtest/run_pgbench.sh <mode> <query>

# 範例
./db/loadtest/run_pgbench.sh baseline student
./db/loadtest/run_pgbench.sh load dashboard
./db/loadtest/run_pgbench.sh stress dashboard
./db/loadtest/run_pgbench.sh spike token
```

環境變數（可覆寫）：`DB_USER` / `DB_NAME` / `DB_CONTAINER`（預設 `database-final-db-1`）。

## 怎麼解讀輸出

pgbench 進度行：
```
progress: 5.0 s, 121.2 tps, lat 8.251 ms stddev 0.132, 0 failed
```
- `tps`：每秒完成交易數 → 越高越好
- `lat`：平均 latency → 越低越好
- `stddev`：latency 抖動 → 越穩越好
- `failed`：失敗交易（連線/鎖/逾時）→ 應為 0；spike 模式可能出現

結尾摘要看 `tps`（含/不含連線建立）與 `latency average`。

## 單連線基準參考值（500 學生 / 17k enrollment，2026-06 實測）

| query | TPS | latency |
|-------|-----|---------|
| simple | ~9500 | 0.10ms |
| student | ~2200 | 0.45ms |
| dashboard | ~121 | 8.25ms ← DB 層最慢 |
| token | ~4200 | 0.24ms |

**關鍵發現**：dashboard 全表聚合比單學生查詢慢約 18 倍，是 DB 層的主要熱點。
學生數放大時這條會線性惡化，是最該關注、最該考慮加索引/物化檢視的查詢。

## 觀察重點

跑 stress/spike 時開另一個終端：
```sh
docker stats --no-stream database-final-db-1   # DB 容器 CPU/記憶體
docker compose exec db psql -U postgres -d dbfinal \
  -c "SELECT count(*) FROM pg_stat_activity;"   # 當前連線數（對照 max_connections，預設 100）
```
spike 的 `-c 200` 會超過預設 `max_connections=100`，預期看到部分連線被拒 → 這正是要觀察的「連線風暴」。
