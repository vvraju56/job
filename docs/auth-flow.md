# Makeable Jobs — Authentication Flow

This document walks through the complete authentication flow across the backend
(FastAPI + JWT), the web client (Next.js), and the mobile client (Flutter).

---

## 1. Overview

Authentication uses a **stateless JWT pair** issued by the FastAPI backend:

| Token          | Claim `type` | Lifetime (default)   | Used for                                    |
| -------------- | ------------ | -------------------- | ------------------------------------------- |
| Access token   | `access`     | 30 minutes           | `Authorization: Bearer <token>` on protected routes |
| Refresh token  | `refresh`    | 14 days              | `POST /auth/refresh` to obtain a new pair   |

Tokens are signed with **HS256** using `SECRET_KEY`. The payload is:

```json
{
  "sub": "<user uuid>",
  "type": "access",            // or "refresh"
  "iat": 1720000000,
  "exp": 1720001800
}
```

Passwords are hashed with **bcrypt** (`hash_password` / `verify_password` in
`backend/app/core/security.py`). The `decode_token` helper validates signature,
expiry, and the expected `type` claim, returning `None` on any failure.

---

## 2. Register → token pair

`POST /api/v1/auth/register`

1. The client sends `{name, email, password}` (email normalized to lowercase,
   password must be 8–128 chars).
2. The backend checks for an existing email → `409` if it already exists.
3. A `User` (profiles) row is created with the bcrypt-hashed password, empty
   `skills`, and default `preferences`.
4. A token pair is minted and returned immediately (**201**):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

> Because a token pair is returned on register, users are signed in immediately —
> there is no separate "verify email" step in the default flow.

---

## 3. Login → token pair

`POST /api/v1/auth/login`

1. Client sends `{email, password}`.
2. `_authenticate` looks up the user by lowercase email, rejects with **401
   "Invalid credentials"** if the user is missing, has no password (e.g.
   social-only account), or the bcrypt check fails.
3. On success a fresh token pair is returned (200).

The login endpoint doubles as the OAuth2 password flow token URL
(`OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")` in `deps.py`).

---

## 4. Refresh

`POST /api/v1/auth/refresh`

1. Client sends `{refresh_token}`.
2. The backend decodes it with `expected_type="refresh"` — a token with
   `type != "refresh"` (or an expired/badly-signed token) is rejected with **401**.
3. The subject (user id) is re-checked against the DB → **401 "User not found"** if
   the user was deleted.
4. A **new access + refresh pair** is returned. Clients must replace both stored
   tokens.

Use refresh when the access token is about to expire or after a 401 on any
protected call.

---

## 5. Logout

`POST /api/v1/auth/logout` (auth required) → **204 No Content**.

Tokens are **stateless JWTs** — there is no server-side revocation store (the code
notes that revocation could be layered with Redis later). Logout therefore means:

1. The client discards its stored access + refresh tokens.
2. Subsequent requests without a valid token get `401`.

---

## 6. Token storage

### 6.1 Web (Next.js)

Two options:

- **httpOnly cookie (recommended):** the access token is set as an httpOnly,
  `SameSite=Lax`/`Secure` cookie so client-side JavaScript cannot read it (XSS
  resistant). The refresh endpoint sets/rotates the cookie. On logout the cookie is
  cleared.
- **In-memory (module-scope variable):** the token lives in a JS variable held by
  the auth provider/store. Simpler, but tokens are lost on full page reload and
  are readable by JS. Use only if you keep everything behind SSR and avoid
  embedding secrets.

The backend is transport-agnostic: it accepts `Authorization: Bearer` headers
regardless of how the client stores the token.

### 6.2 Mobile (Flutter)

- Tokens are persisted in **`shared_preferences`** via `TokenStorage`
  (`mobile/lib/core/storage/token_storage.dart`).
- A **Dio interceptor** (`mobile/lib/core/network/api_client.dart`) attaches
  `Authorization: Bearer <access_token>` to every request.
- On a **401** response the interceptor calls `POST /auth/refresh` with the stored
  refresh token, updates the stored pair, and **retries the original request
  once**. If refresh fails (expired/invalid refresh token) the user is signed out
  and routed to the login screen.
- Store access + refresh keys separately so a failed refresh can clear both.

---

## 7. Protected route behavior on 401

Protected endpoints depend on `get_current_user` (`deps.py`):

1. Extract the Bearer token.
2. `decode_token(token, expected_type="access")` → if invalid/expired/wrong type,
   respond:

```json
HTTP 401
{
  "detail": "Invalid or expired token"
}
WWW-Authenticate: Bearer
```

3. Load the user by `sub`; if the user no longer exists → `401 "User not found"`.

**Client handling of a 401:**

- **Web:** the auth provider's fetch wrapper catches 401 → attempts a single
  refresh → on success retries the request; on failure clears auth state and
  redirects to `/login`.
- **Mobile:** the Dio interceptor does the same single-refresh-retry; if it fails,
  `TokenStorage` is cleared, the Riverpod auth provider resets, and GoRouter
  redirects to the login screen.

### Admin guard

Admin-only routes (all `/admin/*`, plus company write routes) depend on
`get_current_admin`, which first resolves the user then requires `role == "admin"`:

```json
HTTP 403
{
  "detail": "Admin access required"
}
```

---

## 8. Full lifecycle sequence

```
  Client                     Backend (FastAPI)
    │  POST /auth/register        │
    │  {name, email, password}    │
    ├────────────────────────────▶│  hash bcrypt, insert profiles row
    │  201 {access, refresh}      │  mint JWT pair
    │◀────────────────────────────┤
    │                             │
    │  GET /jobs/... (public)     │   no auth required
    │  GET /users/me              │
    │  Authorization: Bearer A1   │
    ├────────────────────────────▶│  decode(A1, "access") → user
    │  200 UserOut                │
    │◀────────────────────────────┤
    │  ... 30 minutes pass ...    │
    │  GET /users/me              │
    │  Authorization: Bearer A1   │  A1 expired
    │◀─────────────────────── 401 │
    │  POST /auth/refresh         │
    │  {refresh_token: R1}        │
    ├────────────────────────────▶│  decode(R1, "refresh") → user
    │  200 {A2, R2}               │
    │◀────────────────────────────┤
    │  GET /users/me              │
    │  Authorization: Bearer A2   │  retry once
    ├────────────────────────────▶│  200 UserOut
    │◀────────────────────────────┤
    │  POST /auth/logout          │
    │  Authorization: Bearer A2   │
    ├────────────────────────────▶│  204 — client discards A2/R2
    │◀────────────────────────────┤
```

---

## 9. Security notes

- Tokens are signed and verified with the same `SECRET_KEY`; keep it secret and
  unique per environment (rotate before production).
- Access token TTL is short (30 min) so a leaked token is low-risk; refresh token
  TTL is 14 days.
- Refresh tokens are full JWTs, not opaque strings. If you need revocable sessions
  later, store token jti/hash in Redis and check it on refresh (the logout comment
  in `auth.py` anticipates this).
- Rate limiting (slowapi, 200/min per IP) applies to auth endpoints too, which
  mitigates brute-force login attempts.
- Registering with an existing email returns `409 Conflict` — never reveal whether
  credentials were "close but wrong" beyond the generic 401 message.