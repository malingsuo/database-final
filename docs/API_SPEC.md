# API Spec

Base path: `/api/auth` (proxied through nginx → auth service)

---

## POST /api/auth/register

Create a new account.

**Request**
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

**Response `201`**
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

**Response `400`**
```json
{ "detail": "Account already exists" }
```

---

## POST /api/auth/login

Login with an existing account. Returns a bearer token.

> Password verification is skipped in prototype — any password accepted if account exists.

**Request**
```json
{
  "email": "user@example.com",
  "password": "any"
}
```

**Response `200`**
```json
{
  "access_token": "<token>",
  "token_type": "bearer"
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

**Headers**
```
Authorization: Bearer <token>
```

**Response `200`**
```json
{
  "id": 1,
  "email": "user@example.com"
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

**Path param**: `account_id` — integer ID of the account to delete.

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

**Response `200`** — token valid; nginx reads `X-Account-ID` from response headers and forwards it to the backend as `X-Account-ID`.

**Response `401`** — token invalid; nginx returns `{"status":"error","message":"Unauthorized"}` to the client.
