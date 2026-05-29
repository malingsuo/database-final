# 前端 ↔ 後端 API 契約

> 給後端團隊參考：前端（`frontend/`，Vue 3 + Element Plus）目前依下列契約開發。
> 標示 ✅ 為後端已實作、🟡 為前端期望但後端需對齊、⚠️ 為已知落差/Bug。
>
> 對應前端型別定義：[`frontend/src/api/types.ts`](frontend/src/api/types.ts)

---

## 1. 路由架構（nginx）

所有請求經 nginx（host 埠 `3030` → 容器 80，見 [`nginx/nginx.conf`](nginx/nginx.conf)）：

| 路徑 | 轉發 | 認證 |
|------|------|------|
| `/` | `frontend:3000` | 無 |
| `/api/auth/*` | `auth:8000` | 公開（不過 `auth_request`） |
| `/api/*`（其餘，如 `/api/check/*`） | `backend:8080` | 先過 `auth_request` → `auth:8000/auth/validate` |

- 前端以 `Authorization: Bearer <token>` 帶 token。
- `auth_request` 驗證成功後，auth 服務需回傳 header `X-User-ID`，nginx 會轉給 backend。

---

## 2. 認證 API（`/api/auth/*`，公開）

> 🟡 前端採 **DB-based、account / password / role** 契約（對齊 `backend` 的 `user` 表：`account` / `password_hash` / `role`）。
> ⚠️ 目前 [`auth/src/main.py`](auth/src/main.py) 仍是 dummy（收 email/phone、回固定 token、`validate` 回 UUID），需改寫成下列契約。

### POST /api/auth/register　🟡
學生註冊（管理員由後端手動建立）。

Request:
```json
{ "account": "112703043", "password": "mypassword", "role": "student" }
```
Response 201:
```json
{ "user_id": 1, "account": "112703043", "role": "student" }
```
錯誤（統一 `{ "detail": "..." }`）：
- 400 帳號已存在
- 400 學號非 112 開頭（目前僅開放 112 學年度入學）
- 400 密碼少於 8 碼

### POST /api/auth/login　🟡
Request:
```json
{ "account": "112703043", "password": "mypassword" }
```
Response 200:
```json
{ "access_token": "<token>", "token_type": "bearer", "role": "student", "user_id": 1 }
```
- 401 帳號或密碼錯誤（不分開提示）

### GET /api/auth/status　🟡（需 Bearer）
Response 200：
```json
{ "user_id": 1, "account": "112703043", "role": "student", "student_id": 3 }
```
- **`student_id`**：學生已上傳資料時請帶上（整數）；尚未上傳則回 `null`。前端用它直接解析該學生的檢核資料。

### POST /api/auth/logout　🟡（需 Bearer）
撤銷目前 token。Response `{ "message": "..." }`。

### GET /auth/validate　⚠️（nginx 內部用）
- 驗證 token，並在 header 回傳 **`X-User-ID` = 整數 `user.id`**。
- ⚠️ 目前回的是 UUID 字串，會導致 `/api/check/upload` 解析 `int(x_user_id)` 失敗。

---

## 3. 畢業檢核 API（`/api/check/*`，需 Bearer）

> ✅ 已實作於 [`backend/src/api/routes/checker.py`](backend/src/api/routes/checker.py)。

### POST /api/check/upload　✅
上傳校務系統匯出的 `exportStudentData.json`。

- Request：`multipart/form-data`，欄位 `file`（`.json`）
- 後端從 nginx 注入的 `X-User-ID` 取得使用者；`account == student_number` 建立關聯
- 入學年度須為 112（取學號前三碼），重複上傳會刪舊重建

Response 200:
```json
{ "student_id": 3, "student_number": "112703043", "chinese_name": "彭啟則", "course_count": 48 }
```
錯誤：400 非 .json／JSON 格式錯誤／入學年非 112

> ⚠️ Bug：[`checker.py`](backend/src/api/routes/checker.py) 呼叫 `import_student_json_from_dict(db, data, user_id=user_id)`，但 [`importer.py`](backend/src/services/importer.py) 的 `import_student_json_from_dict(session, data)` 不收 `user_id`，會 TypeError。需修正函式簽名或呼叫端。

### GET /api/check/{student_id}　✅（path 為整數 `student.id`）
回完整檢核結果（見第 4 節）。
- 404 student_id 不存在
- 🟡 建議：student 角色僅能查自己

### GET /api/check/me　🟡（建議新增）
用 `X-User-ID` → `student.user_id` → 跑檢核，回傳同 `GET /api/check/{id}` 格式；查無學生資料回 404。
- 前端目前流程：優先用 `status.student_id` → 否則本地暫存的 student_id → 否則打 `/api/check/me`（未實作會 404 → 引導上傳）。後端補上任一即可免本地後備。

---

## 4. CheckResult 結構（`GET /api/check/{id}` 回傳）

> 以 [`backend/src/services/checker.py`](backend/src/services/checker.py) 實際輸出為準。

```jsonc
{
  "student": {
    "id": 3, "student_number": "112703043", "chinese_name": "彭啟則",
    "entry_year": 112, "register_major": "資訊科學系",
    "register_double_major": "資訊管理學系", "minor1": "統計學系", "minor2": null,
    "graduation_credit": 128, "total_credits": 102
  },

  // 主修；雙主修(double_major_check, 可為 null)、輔系(minor_checks[]) 同結構
  "major_check": {
    "dept_name": "資訊科學系", "found": true, "no_data": false,
    "total_credits_required": 36, "earned_credits": 27,
    "in_progress_credits": 3, "missing_credits": 6,
    "passed_courses": [
      { "course_name": "資料結構", "course_code": "CS201", "credits": 3,
        "score": "88", "group_label": null, "match_confidence": "exact" }
    ],
    "in_progress_courses": [ /* 同 passed，score 為 null/未到 */ ],
    "missing_courses": [
      { "course_name": "作業系統", "course_code": "CS310", "credits": 3,
        "course_type": "必修", "group_label": null, "match_confidence": "none" }
    ],
    "group_violations": [
      { "group": "群B", "min_courses": 2, "passed_courses": 1,
        "in_progress_courses": 1, "note": "...", "status": "incomplete" }
    ],
    // status ∈ "complete" | "incomplete" | "dept_not_found" | "no_data"
    "status": "incomplete"
  },

  // double_major_check 另含 "type":"double_major" 與 "group_checks":[{group,credits_required,earned_credits,missing_credits,status}]
  "double_major_check": null,
  "minor_checks": [],

  "ge_check": {
    "categories": [
      { "category_name": "藝術與美學", "remark_code": "AE",
        "credits_required": 4, "earned_credits": 2, "missing_credits": 2,
        "courses": [ { "course_name": "...", "course_code": "...", "credits": 2, "score": "通過" } ],
        "status": "incomplete" }
    ],
    "status": "incomplete"
  },

  "pe_check": {
    "required_semesters": 4, "passed_semesters": 3, "missing_semesters": 1,
    "passed_courses": [
      { "course_name": "體育（一）", "course_code": "PE101",
        "academic_year_semester": "1121", "score": "通過" }
    ],
    "in_progress_courses": [], "failed_courses": [],
    "status": "incomplete"
  },

  "summary": {
    "all_complete": false,
    "incomplete_items": ["主系必修", "雙主修", "通識", "體育必修"],
    "elective_credits": {
      "graduation_total": 128, "major_required": 36, "ge_required": 28, "pe_required": 4,
      "elective_required": 60, "total_credits_earned": 102,
      "major_earned": 27, "ge_earned": 13, "pe_earned": 3,
      "elective_earned": 59, "elective_gap": 1,
      "note": "選修應修 = 128 - 主系36 - 通識28 - 體育4 = 60 學分"
    }
  }
}
```

---

## 5. 待後端處理（阻擋前端接真 API 的落差）

1. **auth 改 DB-based**：實作上述 `/api/auth/*`（account/password/role），`/auth/validate` 回 **整數** `X-User-ID`。
2. **user → student_id 解析**：`GET /api/auth/status` 回 `student_id`，或新增 `GET /api/check/me`（擇一）。
3. **修 upload bug**：`checker.py` 對 `import_student_json_from_dict` 的呼叫多傳了 `user_id` 參數。

---

## 6. 前端串接備註

- 錯誤格式統一 `{ "detail": "錯誤說明" }`；HTTP 400/401/403/404/500。
- 前端攔截 401 會自動清 token 並導回登入頁。
- 前端 `baseURL` 為相對路徑（`/api/...`）；dev 透過 vite proxy 轉到 nginx `:3030`（見 [`frontend/vite.config.ts`](frontend/vite.config.ts)）。
- 前端可用 `VITE_USE_MOCK=true` 走離線假資料（[`frontend/src/api/mock.ts`](frontend/src/api/mock.ts)），與後端進度解耦；接真 API 時設為 `false`。
