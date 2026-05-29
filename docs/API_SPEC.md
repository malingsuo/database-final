# API Spec

兩個服務皆經由 nginx 對外，統一在 `/api` 之下：

- **Auth service**（`/api/auth/*`）：註冊 / 登入 / 登出 / 狀態。公開，不需 token。
- **Main backend**（`/api/public/*`、`/api/check/*`、`/api/admin/*`）：檢核與管理。
  - `/api/public/*` 公開、不需 token。
  - 其餘 `/api/*` 受保護：nginx 先呼叫 auth `GET /auth/validate` 驗 token，通過後把
    `X-Account-ID`（帳號 UUID）轉發給 backend；token 無效則回 `401 {"status":"error","message":"Unauthorized"}`。

> 客戶端一律帶 `Authorization: Bearer <token>`（公開端點可省略）。

---

## POST /api/auth/register/student

Register a new student account.

**Request**
```json
{
  "email": "student@nccu.edu.tw",
  "password": "secret",
  "student_id": "109703001",
  "name": "王小明",
  "admission_year": 109
}
```
> `name` is optional.

**Response `201`**
```json
{
  "id": "uuid",
  "email": "student@nccu.edu.tw",
  "role": "student"
}
```

**Response `400`**
```json
{ "detail": "Email or student ID already exists" }
```

---

## POST /api/auth/register/admin

Register a new admin account bound to a department.

**Request**
```json
{
  "email": "admin@nccu.edu.tw",
  "password": "secret",
  "department_id": "703"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "email": "admin@nccu.edu.tw",
  "role": "admin"
}
```

**Response `400`**
```json
{ "detail": "Email already exists or department not found" }
```

---

## POST /api/auth/login

Login with an existing account. Returns a bearer token.

> Password verification is skipped in prototype — any password accepted if account exists.

**Request**
```json
{
  "email": "student@nccu.edu.tw",
  "password": "any"
}
```

**Response `200`**
```json
{
  "access_token": "<token>",
  "token_type": "bearer",
  "role": "student"
}
```

**Response `401`**
```json
{ "detail": "Invalid credentials" }
```

---

## POST /api/auth/logout

Revoke the current token.

**Headers**
```
Authorization: Bearer <token>
```

**Response `200`**
```json
{ "message": "Logged out" }
```

---

## GET /api/auth/status

Return info about the currently authenticated account.

For student accounts, also returns `student_number`, `name`, `admission_year`.
For admin accounts, also returns `administrator_id`, `department_id`, `department_name`.

**Headers**
```
Authorization: Bearer <token>
```

**Response `200`** (student)
```json
{
  "id": "uuid",
  "email": "student@nccu.edu.tw",
  "role": "student",
  "student_number": "109703001",
  "name": "王小明",
  "admission_year": 109,
  "administrator_id": null,
  "department_id": null,
  "department_name": null
}
```

**Response `200`** (admin)
```json
{
  "id": "uuid",
  "email": "admin@nccu.edu.tw",
  "role": "admin",
  "student_number": null,
  "name": null,
  "admission_year": null,
  "administrator_id": "uuid",
  "department_id": "703",
  "department_name": "資訊科學系"
}
```

**Response `401`**
```json
{ "detail": "Invalid or expired token" }
```

---

## DELETE /api/auth/user/{account_id}

Delete an account. Only the owner can delete their own account.

**Headers**
```
Authorization: Bearer <token>
```

**Path param**: `account_id` — UUID of the account to delete.

**Response `200`**
```json
{ "message": "Account deleted" }
```

**Response `403`**
```json
{ "detail": "Forbidden" }
```

---

## GET /auth/validate *(internal)*

Used by nginx `auth_request` to validate a token before forwarding to protected routes.
Not intended to be called directly by clients.

**Headers**
```
Authorization: Bearer <token>
```

**Response `200`** — token valid; nginx reads `X-Account-ID` (UUID) from response headers and forwards it to the backend.

**Response `401`** — token invalid; nginx returns `{"status":"error","message":"Unauthorized"}` to the client.

---
---

# Main backend API

錯誤格式統一為 `{ "detail": "...", "code": "..." }`（例：`NOT_FOUND` / `FORBIDDEN` / `BAD_REQUEST` / `UNAUTHORIZED`）。

## GET /api/public/departments *(public)*

回傳所有系所，供註冊時選擇。不需 token。

**Response `200`**
```json
[
  { "id": "703", "college": "理學院", "name": "資訊科學系" }
]
```

---

## POST /api/check/upload

學生上傳校務匯出的 `exportStudentData.json`，匯入本人的修課資料。

- **僅限本人**：身分取自 nginx 轉發的 `X-Account-ID`，需為 student 角色且已有對應 student 記錄。
- **不會建立帳號**：只更新既有學生的資料與課程。
- **學號需相符**：JSON 內的學號與登入學生的學號不符時擋下。
- 目前僅支援 112 學年度入學學生。

**Headers**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Body**：`file` — `.json` 檔（multipart form field）。

**Response `200`**
```json
{
  "student_id": "112703052",
  "student_number": "112703052",
  "chinese_name": "張竣喆",
  "course_count": 47
}
```

**錯誤**
| 狀態 | 情況 |
|------|------|
| `401` | 未帶 / 無效的登入身分（`X-Account-ID`） |
| `403` | 非學生帳號、查無對應學生，或 JSON 學號與登入學號不符 |
| `400` | 非 `.json`、JSON 格式錯誤，或非 112 學年度資料 |

---

## GET /api/check/{student_id}

回傳該學生的完整畢業檢核結果（`CheckResult`）。

**Response `200`** — 物件含下列頂層鍵：

| key | 說明 |
|-----|------|
| `student` | 學生基本資料與 `total_credits` |
| `major_check` | 主修系所檢核（必修 / 群修 / 缺口 / 群組違規） |
| `double_major_check` | 雙主修檢核（無則 `null`） |
| `minor_checks` | 各輔系檢核陣列 |
| `ge_check` | 通識：各類別 `credits_required_min/max`、`earned_credits`、`core_domains`、`cross_domain_courses` 等 |
| `pe_check` | 體育學期數 |
| `summary` | `all_complete`、`incomplete_items`、`elective_credits`（選修缺口） |

> 完整範例見 [`docs/bruno-api/check.yml`](bruno-api/check.yml)。

**Response `404`**
```json
{ "detail": "Student id=... 不存在", "code": "NOT_FOUND" }
```

---

## GET /api/admin/dashboard

管理員工作臺彙總。

**Response `200`**
```json
{
  "total_students": 2,
  "on_track_students": 2,
  "at_risk_students": 0,
  "pass_rate": 100,
  "risk_students": [ /* 至多 5 筆 status=at_risk 的 profile，依學分進度由低到高 */ ],
  "difficult_courses": [
    { "name": "自然語言處理", "total": 2, "failed": 2, "fail_rate": 100 }
  ]
}
```
> `difficult_courses`：依全體修課紀錄計算各課程未通過率，取前 3 名。

---

## GET /api/admin/students

學生列表（每位回 profile 彙總）。

**Query**（皆選填）：`q`（學號或姓名模糊比對）、`admission_year`、`status`（`on_track` / `at_risk`）。

**Response `200`** — `profile` 物件陣列：
```json
[
  {
    "student_id": "112703043",
    "name": "彭啟則",
    "admission_year": 112,
    "status": "on_track",
    "notes": null,
    "double_major": true,
    "total_credits": 116.0,
    "required_credits": 128,
    "completed_courses": 46,
    "failed_courses": 13
  }
]
```
| 欄位 | 說明 |
|------|------|
| `status` | 系辦標記：`on_track` / `at_risk`（預設 `on_track`） |
| `notes` | 系辦備註（可為 `null`） |
| `double_major` | 是否有雙主修（由 `fields_of_study` 推導） |
| `total_credits` | 已通過課程學分總和 |
| `required_credits` | 畢業總學分（128） |
| `completed_courses` | 已通過課程數 |
| `failed_courses` | 未通過課程數（`is_passed=false`，含尚未取得成績者） |

---

## GET /api/admin/students/{sid}

單一學生的 profile 加上完整檢核結果。

**Response `200`**
```json
{
  "profile": { /* 同上 profile 物件 */ },
  "check": { /* 同 GET /api/check/{student_id} 的 CheckResult */ }
}
```

**Response `404`**
```json
{ "detail": "Student id=... 不存在", "code": "NOT_FOUND" }
```

---

## PATCH /api/admin/students/{sid}

更新系辦對學生的標記與備註。`status`、`notes` 皆選填，僅更新有帶的欄位。

**Request**
```json
{ "status": "at_risk", "notes": "必修多次未過，需安排輔導" }
```

**Response `200`** — 更新後的 `profile` 物件。

**錯誤**
| 狀態 | 情況 |
|------|------|
| `404` | 查無學生 |
| `400` | `status` 非 `on_track` / `at_risk` |

> 註：`/api/admin/*` 目前僅靠 nginx 驗 token，**尚未檢查 admin 角色**（任何已登入帳號皆可呼叫）。
