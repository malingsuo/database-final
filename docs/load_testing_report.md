# 壓力測試報告 — 畢業學分審核系統

> 測試日期：2026-06　｜　分支：feat/k6-load-testing
> 工具：k6 v2.0.0（HTTP 全鏈路）＋ pgbench 18.4（資料庫層）
> 環境：本機 Docker Compose，單機 8 核 / 7.6 GiB

---

## 1. 系統架構與壓測策略

```
使用者 → nginx(:3030) → auth(:8000)   ← FastAPI async + asyncpg
                      → backend(:8080) ← FastAPI sync  + psycopg2  ← PostgreSQL(:5432)
                      → frontend(:3000)
```

關鍵成本特性（決定壓測怎麼設計、數字怎麼解讀）：

| 元件 | 特性 | 對壓測的影響 |
|------|------|-------------|
| **backend** | `uvicorn.run(app)` **單 worker**、sync(psycopg2) | 單進程處理所有請求，CPU 跑滿一核即飽和，是主要瓶頸 |
| **auth** | 單 worker，登入用 **argon2**(m=64MB,t=3,p=4) | argon2 故意 CPU+記憶體密集，瞬間大量登入最易雪崩 |
| **check_graduation** | 讀 JSON 規則 + 三層課程比對 + 通識 DFS（純 CPU） | 重在 backend CPU，不是 DB；有 lru_cache 加持 |
| **nginx auth_request** | 每個受保護 API 先打 auth 驗 token | 隱性放大 auth 負載 |
| **PostgreSQL** | `max_connections=100`（保留 3 給 superuser） | 連線數硬上限，高並發需連線池 |

採用兩套互補測試：
- **k6**：打 nginx，測「整條 HTTP 鏈」的真實使用者體驗
- **pgbench**：直連 5432，隔離測「資料庫本身」的極限

---

## 2. 資料準備

灌入 500 名假學生（`scripts/seed_load_test_data.py --count 500`）：
- 學號 `112703101`~`112703600`（資科系 112 學年格式，避開真實學號 112703043）
- 統一密碼 `loadtest123`，帳號 `loadtest_stu101@test.local`~
- 16,996 筆 enrollment（從真實 703 系課程取樣，grade 分布 80% 通過 / 10% 不及格 / 10% 修課中）
- advisor_status 70% on_track / 30% at_risk（讓 dashboard 統計有差異）

資料規模：student 501、enrollment 16,996、course 33,775、token 7,573。

---

## 3. 資料庫層壓測（pgbench）

直連 PostgreSQL，跳過應用層。四種查詢對應系統真實熱點：

| query | 對應系統操作 |
|-------|-------------|
| simple | `GET /api/public/departments`（260 筆讀） |
| student | check_graduation 撈學生修課（enrollment×course 複合 JOIN） |
| dashboard | admin dashboard 課程失敗率（全表 GROUP BY + 條件聚合） |
| token | auth 驗證 SELECT + 登入 INSERT |

### 3.1 baseline — 單連線基準（-c 1, 20s）

| query | TPS | 平均 latency | 意義 |
|-------|-----|-------------|------|
| simple | ~9,500 | 0.10 ms | DB 處理簡單讀極快 |
| student | ~2,200 | 0.45 ms | 複合 key JOIN 仍很快 |
| **dashboard** | **~121** | **8.25 ms** | **DB 層最慢，比單學生查詢慢約 18 倍** |
| token | ~4,200 | 0.24 ms | 含 INSERT 仍快 |

模擬情境：系統完全沒有並發時，每一種 DB 操作的「最快可能速度」。dashboard 聚合明顯是最重的查詢。

### 3.2 load — 穩定並發（-c 20 -j 4, 60s，student query）

| 指標 | 數值 |
|------|------|
| TPS | ~9,000（從單連線 2,200 提升） |
| 平均 latency | ~2 ms |
| 失敗 | 0 |

模擬情境：約 20 個並發查詢持續打 DB（穩態營運）。結論：對輕量 JOIN，DB 並發擴展性良好（單連線 2,200 → 20 連線 9,000 TPS）。

### 3.3 stress — 連線數階梯爬升（dashboard query，各 30s）

| 連線數 | TPS | 平均 latency | 觀察 |
|--------|-----|-------------|------|
| 1 | 121 | 8.25 ms | 基準 |
| 30 | ~380 | 79 ms | **TPS 峰值附近** |
| 60 | ~353 | 170 ms | ⚠️ TPS 不升反降，latency 翻倍 |
| 100 | — | — | ❌ `FATAL: sorry, too many clients already` |

模擬情境：管理員端同時湧入愈來愈多人看 dashboard。
結論：**dashboard 聚合的並發拐點約在 30 連線**，超過後 TPS 不增、latency 暴增；100 連線直接撞 `max_connections` 上限。

### 3.4 spike — 連線建立風暴（-c 90 -C 每筆重建連線, 30s，token query）

| 指標 | 持久連線(baseline) | 每筆重建連線(spike) | 倍數 |
|------|-------------------|---------------------|------|
| 平均 latency | 0.24 ms | **48.5 ms** | ~200× |
| TPS | ~4,200 | ~1,300 | ↓ 69% |
| 連線建立時間 | — | 6.0 ms | — |

模擬情境：應用層不用連線池、每個請求都開新 DB 連線（PostgreSQL 每連線 fork 一個 process）。
結論：**連線建立成本遠大於查詢本身**，不用連線池會讓 latency 暴增約 200 倍。

### 3.5 DB 層三大結論

1. **dashboard 全表聚合是 DB 最大熱點**（baseline 已慢 18 倍），學生數放大會線性惡化 → 建議加索引或物化檢視（materialized view）。
2. **連線拐點約 30、硬上限 100**（max_connections）→ 高並發需 PgBouncer 連線池或調高上限。
3. **連線池是必要的**：每請求開新連線會讓 latency 暴增 200 倍。

---

## 4. HTTP 全鏈路壓測（k6）

透過 nginx 打 API，測整條鏈的真實使用者體驗。資源欄為壓測尖峰段 `docker stats` 實測。

### 4.1 baseline — 純查詢基準（departments，ramp 20→50→100 VU，~3min）

| 指標 | 數值 |
|------|------|
| 吞吐 | 322 req/s |
| latency p95 / max | 315 ms / 700 ms |
| 失敗率 | 0% |
| 尖峰資源 | **backend CPU 110%**（單 worker 跑滿一核）、db 28%、nginx 4% |

模擬情境：大量使用者狂刷免登入的系所列表（無 sleep）。
結論：即使最簡單的查詢，瓶頸也在 **backend 單 worker 的 CPU**（Python 處理 + 序列化），不是 DB。

### 4.2 browse — 登入一次後持續瀏覽（ramp→100 VU，~6min）

| 指標 | 數值 |
|------|------|
| 吞吐 | 27 req/s（含 1~4s 閱讀停頓） |
| 整體 latency median / p95 / max | 16.7 ms / 691 ms / 9.8 s |
| check latency median / p95 | 20.8 ms / 1,007 ms |
| login（每 VU 僅 1 次） p95 | 339 ms |
| 失敗率 / checks | 0% / 100% |
| 尖峰資源 | backend 23%、auth 6%、db 11%（很輕鬆） |

模擬情境：100 名學生登入後，在 session 內反覆看檢核/盤點/切分頁（最貼近真實使用）。
結論：**已登入使用者的正常瀏覽，系統游刃有餘**（median 僅 16ms）。p95/max 的拖尾來自暖機時 100 VU 同時登入那一刻的 argon2 排隊，穩態後極快。

### 4.3 load — 每輪都重新登入的混合場景（ramp→60 VU，~6min）

| 指標 | 數值 |
|------|------|
| 吞吐 | 25.8 req/s |
| 整體 latency median / p95 / p99 | 491 ms / 1.68 s / 2.35 s |
| login p95 | 1.66 s |
| check p95 | 1.69 s |
| 失敗率 | 0.07%（7/9373，登入超時） |
| 尖峰資源 | **auth CPU 306%**（argon2 吃滿 3 核）、backend 9%、db 7% |

模擬情境：每個動作前都重新登入（最壞情況 / 無 session 重用）。
結論：**頻繁登入時瓶頸 100% 在 auth 的 argon2**，與 backend/DB 無關。對比 browse（median 16ms）慢 30 倍，差別全在每輪 argon2。check 被拖慢也是因 auth 飽和拖累整條鏈。

### 4.4 spike — 瞬間登入暴衝（10s 內衝到 300 VU，~2.3min）

| 指標 | 數值 |
|------|------|
| login latency avg / median / p95 / max | 12.5 s / 16.4 s / 30.8 s / 34.9 s |
| 失敗率 | 9.42%（150/1592 登入超時或被拒） |
| checks 通過率 | 90.57% |
| 尖峰資源 | **auth CPU 375%**（argon2 達上限近 4 核）、記憶體 271 MB、backend/db ~0% |

模擬情境：開放查詢的瞬間「全班同時湧入登入」。
結論：**argon2 在瞬間尖峰下雪崩**——登入要等 16~35 秒、近 1 成失敗。這是系統最脆弱的點。

### 4.5 stress — 推到極限（學生檢核 ramp→500 VU + admin dashboard 並發，~8min）

| 指標 | 數值 |
|------|------|
| 整體 latency median / p95 / max | 5.27 s / 30.67 s / 31.85 s |
| 失敗率 | 7.78%（885/11366） |
| login 成功率 | 92%（5406 ✓ / 468 ✗） |
| check 成功率 | 91%（4690 ✓ / 412 ✗） |
| **dashboard 成功率** | **99%（194 ✓ / 1 ✗）** |
| students 列表成功率 | 97%（191 ✓ / 4 ✗） |
| 吞吐 | 23.6 req/s |

模擬情境：500 名學生同時湧入（持續登入+看檢核），同時 5 名管理員看 dashboard。
結論：系統在 500 VU 持續登入下**嚴重過載**（p95 30s、~8% 失敗）。值得注意：**admin dashboard 在此壓力下仍 99% 成功**，證明過載主因不是 DB 聚合，而是 argon2 登入——與 load/spike 結論一致。

### 4.6 HTTP 層核心結論

1. **argon2 登入是全系統最脆弱點**：load 時 auth 吃滿 3 核、spike/stress 時雪崩到 30s+ latency 與 ~8% 失敗。
2. **backend 與 auth 都是單 worker**：無法吃滿多核，是擴展上限的根因。
3. **真實使用（登入後瀏覽）其實很輕鬆**：問題集中在「登入動作」本身，不是日常瀏覽或 DB 查詢。

---

## 5. 綜合結論

### 5.1 兩套測試的交叉驗證

| 層面 | k6（HTTP 全鏈路）| pgbench（DB 隔離）| 一致結論 |
|------|------------------|-------------------|----------|
| 最大瓶頸 | argon2 登入（auth 單 worker） | 連線數上限 100 + dashboard 聚合 | 應用層瓶頸先於 DB 瓶頸 |
| dashboard | stress 下仍 99% 成功 | 單連線 8.25ms、拐點 ~30 連線 | DB 聚合非系統當前主因，但是 DB 內最重查詢 |
| 真實瀏覽 | median 16ms，輕鬆 | JOIN 0.45ms、20 連線 9000 TPS | 日常使用完全沒問題 |

### 5.2 系統可承受範圍（本機環境）

- **舒適區**：~100 名已登入使用者同時瀏覽 → median 16ms，毫無壓力。
- **警戒區**：~60 名持續重新登入 → p95 1.7s，auth 吃滿 3 核。
- **過載區**：瞬間 300+ 同時登入 / 持續 500 VU → latency 16~31s、~8% 失敗。

### 5.3 優化建議（依投資報酬率排序）

1. **auth / backend 改多 worker**（`uvicorn --workers N` 或 gunicorn）：單 worker 是擴展上限根因，最低成本最大效益。
2. **降低 argon2 成本或加登入節流**：argon2 參數（m=64MB）對畢業檢核這類低敏系統偏重，可調低；或對登入加 rate limit / 驗證碼防瞬間暴衝。
3. **DB 加連線池（PgBouncer）**：避免每請求開新連線（實測 latency 差 200 倍），並緩解 max_connections=100 上限。
4. **dashboard 聚合加索引或物化檢視**：學生數放大時這條會線性惡化，提前準備。

---

## 附錄：如何重現

```sh
# 前置
docker compose up -d --build
cd backend && set -a && source ../.env && set +a
uv run python ../scripts/seed_load_test_data.py --count 500

# DB 層（pgbench）
./db/loadtest/run_pgbench.sh baseline dashboard
./db/loadtest/run_pgbench.sh load student
./db/loadtest/run_pgbench.sh stress dashboard
./db/loadtest/run_pgbench.sh spike token

# HTTP 層（k6）
k6 run k6/baseline.js
k6 run k6/browse.js
k6 run k6/load.js
k6 run k6/spike.js
k6 run k6/stress.js
```

詳細腳本說明見 `k6/README.md` 與 `db/loadtest/README.md`。
