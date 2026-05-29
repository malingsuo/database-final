# 系統總覽：NCCU 畢業學分檢核系統

## 專案目標

學生上傳 iNCCU `exportStudentData.json`，系統自動比對主系、雙主修、輔系、通識、體育是否達畢業標準，回傳結構化結果。

目前範圍：112 學年度入學、全校各系所學生。

---

## 原始版本（final/）進度 summary

### DB 設計（4 張 table）

| Table | 用途 |
|---|---|
| `user` | 帳號層，學生 / 管理員共用，存 account / password_hash / role |
| `student` | 學生資料，1:1 對應 user，存學號、主修、雙主修、輔系、學分統計 |
| `admin` | 管理員，1:1 對應 user，綁定系所 dept_code |
| `student_course` | 修課紀錄 N:1 student，存課號、課名、學分、成績、必/群/選 |

畢業規則**不進 DB**，全部存 JSON，checker 啟動時 `lru_cache` 讀入。

### 畢業規則 JSON

| 類型 | 路徑 | 數量 |
|---|---|---|
| 主系畢業規定 | `data/graduation_requirements/112/` | 48 個系所 |
| 雙主修規定 | `data/double_major_requirements/112/` | 46 個（含 783_AI學程_cs / non_cs）|
| 輔系規定 | `data/minor_requirements/112/` | 38 個 |
| 通識規定 | `data/graduation_requirements/112/ge_requirements.json` | 1 個 |
| 體育規定 | `data/graduation_requirements/112/pe_requirements.json` | 1 個 |

### 核心邏輯（checker.py，836 行）

| 函式 | 功能 |
|---|---|
| `check_major` | 主系必修/群修比對，支援 group_rules 分組門數驗證 |
| `check_double_major` | 雙主修；AI 學程依主修是否資訊系自動選 cs/non_cs JSON |
| `check_minor` | 輔系檢核 |
| `check_ge` | 通識，依 remark_code 對應類別學分 |
| `check_pe` | 體育必修（需 4 學期通過）|
| `check_graduation` | 主入口，整合全部結果 + 計算選修學分缺口 |

課程比對策略（依序）：
1. `course_code` 精確比對
2. 課名正規化後子字串比對
3. difflib fuzzy ratio ≥ 0.85

### API

| Method | Path | 說明 |
|---|---|---|
| POST | `/api/check/upload` | 上傳 exportStudentData.json |
| GET | `/api/check/{sid}` | 取得學生完整畢業檢核結果 |

---

## 搬移對照表（final/ → database-final/）

| 原始位置 | 搬到 | 備註 |
|---|---|---|
| `docs/data/graduation_requirements/` | `data/graduation_requirements/` | 完整 48 個 |
| `docs/data/double_major_requirements/` | `data/double_major_requirements/` | 完整 46 個 |
| `docs/data/minor_requirements/` | `data/minor_requirements/` | 完整 38 個 |
| `app/models/models.py` | `src/models/models.py` | 無異動 |
| `app/services/checker.py` | `src/services/checker.py` | `_DATA_DIR` 改讀 `DATA_DIR` 環境變數，fallback 相對路徑 |
| `app/services/importer.py` | `src/services/importer.py` | 無異動 |
| `app/core/config.py` | `src/core/config.py` | DATABASE_URL 改從環境變數組裝（PostgreSQL）|
| `app/core/database.py` | `src/core/database.py` | 無異動 |
| `app/core/exceptions.py` | `src/core/exceptions.py` | 無異動 |
| `app/api/routes/checker.py` | `src/api/routes/checker.py` | 加 `X-User-Id` header（nginx 傳入）|
| `app/api/router.py` | `src/api/router.py` | 無異動 |
| `k6/smoke_test.js` | `k6/smoke_test.js` | URL 改 `localhost:3030/health` |
| _(新增)_ | `db/init.sql` | PostgreSQL DDL，docker-compose 啟動自動執行 |

**未搬移：**
- `core/logging.py`（structlog 結構化 log，不影響功能）
- `scripts/verify_*.py`（爬蟲驗證工具，路徑寫死在本機）

---

## 現在的架構

```
database-final/
├── auth/               # 同事實作：FastAPI + asyncpg + argon2，負責 register / login / token
├── backend/            # 我們實作：FastAPI + SQLAlchemy，負責畢業檢核
│   └── src/
│       ├── main.py
│       ├── api/routes/checker.py
│       ├── core/           # config / database / exceptions
│       ├── models/         # user / student / admin / student_course
│       └── services/       # checker.py / importer.py
├── frontend/           # Vue 3（骨架，尚未開發）
├── nginx/              # reverse proxy，/api/auth/ → auth，/api/ → backend（需驗 token）
├── data/               # 畢業規則 JSON（不進 DB）
│   ├── graduation_requirements/112/
│   ├── double_major_requirements/112/
│   └── minor_requirements/112/
├── db/
│   └── init.sql        # 建表 DDL，container 啟動自動執行
├── k6/
│   └── smoke_test.js
└── docker-compose.yml
```

## 尚未完成

- auth service 的 `user` 與 backend 的 `user` table 對接（user_id FK 流程）
- 上傳前需先登入（auth guard on upload endpoint）
- 管理員 CRUD API（查看 / 刪除特定系所學生）
- 前端頁面
