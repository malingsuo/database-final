# k6 壓力測試

針對畢業學分審核系統的分層壓測。透過 nginx(3030) 打 API，與真實使用者路徑一致。

## 前置作業

1. 啟動系統：
   ```sh
   docker compose up -d --build
   ```

2. 灌假學生資料（dashboard / DB 壓測需要差異化資料）：
   ```sh
   cd backend
   set -a && source ../.env && set +a
   uv run python ../scripts/seed_load_test_data.py --count 500
   ```
   - 學號 `112703101` ~ `112703600`（資科系 112 學年格式，避開真實 `112703043`）
   - 帳號 `loadtest_stu101@test.local` ~ `loadtest_stu600@test.local`
   - 統一密碼 `loadtest123`
   - 流水號 3 碼，上限 899 名（101~999）
   - 清除：`uv run python ../scripts/seed_load_test_data.py --clean`（只刪 `loadtest_stu*`，不動真實學生）

3. 安裝 k6：`brew install k6`

## 四個腳本（由淺入深）

| 腳本 | 目的 | 主壓端點 |
|------|------|----------|
| `baseline.js` | 乾淨基準線 | `GET /api/public/departments`（免驗證、簡單查詢） |
| `load.js` | 真實混合場景，找拐點 | 登入 → `GET /api/check/{sid}`（畢業檢核，CPU 重） |
| `stress.js` | 推到極限 | 學生檢核 + `GET /api/admin/dashboard`（聚合查詢） |
| `spike.js` | 瞬間流量尖峰 | `POST /api/auth/login`（argon2，最脆弱點） |

## 執行

```sh
# 基準線
k6 run k6/baseline.js

# 負載（可調假學生數量範圍）
k6 run -e STU_COUNT=500 k6/load.js

# 壓力（含 admin 情境需提供 admin 帳密；不提供則只跑學生情境）
k6 run -e ADMIN_EMAIL=admin703@nccu.local -e ADMIN_PASSWORD=<pw> k6/stress.js

# 尖峰
k6 run k6/spike.js
```

### 可用環境變數（`-e KEY=VALUE`）

| 變數 | 預設 | 說明 |
|------|------|------|
| `BASE_URL` | `http://localhost:3030` | 系統入口（nginx） |
| `STU_START` | `101` | 假學生流水號起點 |
| `STU_COUNT` | `500` | 假學生數量（需與 seed 的 `--count` 一致） |
| `STU_PASSWORD` | `loadtest123` | 假學生統一密碼 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | 空 | stress.js 的 admin 情境用 |

## 系統壓測點對照（為何這樣設計）

- **backend 是 sync（psycopg2）worker** → 高並發下 worker/連線池最易飽和，`load`/`stress` 主壓這裡。
- **check_graduation 是 CPU 密集**（讀 JSON 規則 + 三層課程比對 + 通識 DFS 分配），不是純 DB query。
- **argon2 登入故意 CPU+記憶體密集**（m=64MB,t=3,p=4）→ `spike` 專門壓這點，最容易被瞬間流量打垮。
- **每個受保護 `/api/` 都觸發 nginx auth_request** 查 token 表 → 隱性壓 auth service。
- **DB 層**透過上層 API 間接壓：enrollment×course 複合 JOIN（讀）、dashboard 聚合（GROUP BY/SUM）、token 表高頻讀寫、連線池上限。

## 閾值（thresholds）說明

各腳本內建 SLO 門檻，跑完若紅字 `thresholds ... have been crossed` 代表超出該門檻：

- baseline：p95 < 300ms（簡單查詢應很快）
- load：整體 p95 < 800ms；login p95 < 1500ms（argon2 放寬）；check p95 < 1000ms
- stress：門檻刻意放寬（目的是「找」極限，看趨勢圖而非全綠）
- spike：重點看會不會雪崩與回復速度，門檻寬鬆

## 觀察重點

跑測同時開另一個終端看資源：
```sh
docker stats --no-stream    # 看 auth / backend / db 容器 CPU/記憶體
docker compose logs -f backend   # 看請求是否塞住 / 報錯
```
