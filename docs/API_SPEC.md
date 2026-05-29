# API Spec

Base path: `/api/auth` (proxied through nginx → auth service)

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
