# Makeable Jobs — API Reference

> Base URL: `https://<api-host>/api/v1` (locally `http://localhost:8000/api/v1`)

The Makeable Jobs backend is a FastAPI application exposing a REST API under the
`/api/v1` prefix. Interactive documentation is available at:

| Resource         | URL                                  |
| ---------------- | ------------------------------------ |
| Swagger UI       | `/docs`                              |
| ReDoc            | `/redoc`                             |
| OpenAPI JSON     | `/api/v1/openapi.json`               |
| Health check     | `/health`                            |
| Root banner      | `/`                                  |

All timestamps are returned in ISO-8601 / RFC 3339 format in UTC. All identifiers
are UUIDs (as strings).

---

## 1. Authentication

All endpoints marked **Auth required** must send the access token as a Bearer token:

```
Authorization: Bearer <access_token>
```

The token is a **stateless JWT** signed with HS256. It carries the user id in the
`sub` claim and a `type` claim (`"access"` or `"refresh"`).

### Token lifecycle

| Item                 | Value                                  |
| -------------------- | -------------------------------------- |
| Access token TTL     | 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Refresh token TTL    | 14 days (`REFRESH_TOKEN_EXPIRE_DAYS`)  |
| Signing algorithm    | HS256 (`ALGORITHM`)                    |
| Secret               | `SECRET_KEY`                           |
| Password hashing     | bcrypt                                 |

### Refresh flow

1. The access token expires after 30 minutes.
2. The client calls `POST /auth/refresh` with the still-valid refresh token.
3. The API returns a **new access/refresh pair**; the client replaces both.

> Note: Because tokens are stateless, `POST /auth/logout` does not revoke a token
> server-side — clients must discard their stored tokens. (Revocation can be layered
> on later with Redis denylists.)

### Request body example (refresh)

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## 2. Error handling conventions

Errors are returned using FastAPI's `HTTPException` JSON shape:

```json
{
  "detail": "Job not found"
}
```

| Code | Meaning                                        | Common triggers                                                        |
| ---- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| 400  | Bad request                                    | Non-UTF-8 resume upload, invalid role value on admin role change        |
| 401  | Unauthenticated                                | Missing/invalid/expired token, wrong credentials, bad refresh token     |
| 403  | Forbidden                                      | Calling an admin endpoint as a non-admin user                           |
| 404  | Not found                                      | Job, company, application, notification, or alert does not exist        |
| 409  | Conflict                                       | Registering with an email that already exists                           |
| 413  | Payload too large                              | Resume upload larger than 2 MB                                          |
| 422  | Unprocessable entity (Pydantic validation)     | Malformed body, wrong types, out-of-range query params                  |
| 429  | Too many requests (slowapi)                    | Exceeding the rate limit                                                |
| 500  | Internal server error                          | Unhandled exception                                                     |

Pydantic validation errors (422) use FastAPI's detailed format listing each field
problem.

### Rate limiting

The whole API is rate limited per client IP to **200 requests / minute**
(`Limiter(default_limits=["200/minute"])`, keyed by remote address via slowapi).
When exceeded, the API responds with `429 Too Many Requests`.

### CORS

CORS is configured from `CORS_ORIGINS` (comma-separated). Defaults include
`http://localhost:3000` and `https://makeable-jobs.vercel.app`. Credentials are
allowed; all methods and headers are permitted.

---

## 3. Auth endpoints

### `POST /auth/register` — create an account

No auth required. Returns a token pair (201).

**Request body**

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "supersecret123"
}
```

Constraints: `name` 1–255 chars, `email` must be valid, `password` 8–128 chars.
Emails are stored lowercase. New users get default preferences
(`{"remote_only": false, "job_types": [], "locations": [], "keywords": []}`).

**Response 201**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** `409` if the email is already registered.

### `POST /auth/login` — log in

No auth required. Returns a token pair.

**Request body**

```json
{
  "email": "ada@example.com",
  "password": "supersecret123"
}
```

**Response 200** — same `TokenPair` shape as register.

**Errors:** `401` for invalid credentials.

### `POST /auth/refresh` — rotate tokens

No auth required. Accepts a refresh token and returns a fresh token pair.

**Request body**

```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIs..." }
```

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** `401` if the refresh token is invalid/expired or the user no longer exists.

### `POST /auth/logout` — sign out

**Auth required.** Returns 204 with no body. Tokens are stateless; the client
discards them locally.

### `GET /auth/me` — current user

**Auth required.** Returns the `UserOut` for the authenticated user.

**Response 200**

```json
{
  "id": "7c3f6a2e-...",
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "avatar": null,
  "headline": "Full-Stack Engineer",
  "bio": null,
  "skills": ["Python", "FastAPI"],
  "experience": 3,
  "location": "Bengaluru, India",
  "resume_url": null,
  "preferences": { "remote_only": false, "job_types": [], "locations": [], "keywords": [] },
  "role": "user",
  "created_at": "2026-07-20T09:12:00Z"
}
```

---

## 4. Jobs endpoints

### `GET /jobs` — search jobs

No auth required. Full-text-ish search with filters, sorting, and pagination.

**Query parameters**

| Parameter       | Type    | Description                                                      |
| --------------- | ------- | ---------------------------------------------------------------- |
| `q`             | string  | Free-text query (max 200) matched against title, company, description |
| `location`      | string  | Substring match on location                                       |
| `remote`        | boolean | `true` filters to remote jobs                                     |
| `salary_min`    | number  | Jobs whose `salary_max >= salary_min`                             |
| `salary_max`    | number  | Jobs whose `salary_min <= salary_max`                             |
| `job_type`      | string  | `full_time` \| `part_time` \| `contract` \| `internship` \| `freelance` |
| `level`         | string  | `entry` \| `mid` \| `senior` \| `lead` \| `executive`             |
| `experience_min`| integer | Jobs whose `experience_max >= experience_min`                     |
| `experience_max`| integer | Jobs whose `experience_min <= experience_max`                     |
| `source`        | string  | `linkedin` \| `indeed` \| `naukri` \| `internshala` \| `wellfound` \| `company` \| `manual` \| `serpapi` \| `usajobs` \| `jsearch` \| `greenhouse` \| `ashby` \| `remoteok` |
| `company`       | string  | Substring match on company name                                   |
| `sort`          | string  | `recent` (default) \| `salary_desc` \| `salary_asc` \| `relevance` |
| `page`          | integer | 1-based page number (default 1)                                   |
| `page_size`     | integer | Items per page, 1–100 (default 20)                                |

> `sort=relevance` only re-ranks results when a `q` is supplied (title matches rank
> first, then recency).

**Response 200**

```json
{
  "total": 3,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "e8b4f2a1-...",
      "source": "linkedin",
      "title": "Software Engineer",
      "description": "Build cloud-native products...",
      "company_id": "3c9d1b77-...",
      "company_name": "Nova Labs",
      "company_logo": "https://cdn.example.com/nova.png",
      "location": "Bengaluru, India",
      "remote": false,
      "salary_min": 1200000.0,
      "salary_max": 2400000.0,
      "salary_currency": "INR",
      "salary_text": "₹12L – ₹24L/yr",
      "job_type": "full_time",
      "level": "mid",
      "skills": ["TypeScript", "React", "SQL"],
      "apply_url": "https://www.linkedin.com/jobs/view/123456",
      "apply_on": "LinkedIn",
      "experience_min": 2,
      "experience_max": 6,
      "posted_at": "2026-08-10T10:30:00Z",
      "sponsored": false,
      "views": 120
    }
  ]
}
```

### `GET /jobs/trending` — most-viewed jobs

No auth required. `limit` (1–30, default 6) ordered by `views` descending, then recency.

**Response 200** — array of `JobOut`.

### `GET /jobs/recommended` — personalized recommendations

**Auth required.** Uses the user's `skills` plus preference `keywords` (matched
against company name) and `remote_only`. `limit` 1–30 (default 8).

**Response 200** — array of `JobOut`.

### `GET /jobs/search-suggestions` — autocomplete

No auth required. `q` (1–100 chars) and `limit` (1–20, default 8). Returns the most
frequent matching job titles.

**Response 200**

```json
["Software Engineer", "Software Engineering Intern", "Senior Software Engineer"]
```

### `GET /jobs/{job_id}` — job detail

No auth required. Increments the job `views` counter by 1.

**Response 200** — `JobOut`.

**Errors:** `404` if the job does not exist or is inactive.

### `POST /jobs/{job_id}/save` — save a job

**Auth required.** Returns 201. Idempotent — saving twice still returns
`{"saved": true}` (enforced by the `saved_jobs.user_id, job_id` unique constraint).

**Response 201**

```json
{ "saved": true }
```

**Errors:** `404` if the job does not exist.

### `DELETE /jobs/{job_id}/save` — unsave a job

**Auth required.** Returns 204. No-op if the job was not saved.

### `GET /jobs/{job_id}/similar` — similar jobs

No auth required. `limit` 1–20 (default 5). Matches other active jobs whose title
contains the last word of this job's title, newest first.

**Response 200** — array of `JobOut`.

### `POST /jobs/track-search` — record a search

**Auth required.** Query parameters: `q` (1–200 chars, required) and `filters`
(optional JSON string, e.g. `{"remote": true}`). Persists the search into the
user's history.

**Response 201**

```json
{ "tracked": true }
```

### `GET /jobs/search` — multi-source search (6 providers)

No auth required. The primary search the web app and Flutter app use. Fans the
search out to **every enabled provider** concurrently, normalizes and merges the
results, removes duplicates across sources, persists them into the `jobs` table
(`source` = provider name), caches identical searches for 6 hours, and enforces
the SerpApi monthly budget. API keys never leave the backend.

Supported providers (see `ENABLED_PROVIDERS`; the first four answer keyword
searches, Greenhouse/Ashby join when a `company` filter is supplied):

| Provider     | Source value    | Key required | Notes                             |
| ------------ | --------------- | ------------ | --------------------------------- |
| SerpApi      | `serpapi`       | `SERPAPI_API_KEY` | Google Jobs engine; ~250 free searches/month |
| JSearch      | `jsearch`       | `JSEARCH_API_KEY` | multi-source                      |
| USAJobs      | `usajobs`       | `USAJOBS_API_KEY` + `USAJOBS_EMAIL` | federal jobs             |
| Remote OK    | `remoteok`      | none         | remote-first feed                 |
| Greenhouse   | `greenhouse`    | none         | ATS board (company filter only)   |
| Ashby        | `ashby`         | none         | ATS board (company filter only)   |

**Deduplication** happens across sources on (title, company, location, apply
URL) with priority: SerpApi > JSearch > Greenhouse > Ashby > USAJobs > Remote OK.

If **no** provider is configured, the endpoint transparently falls back to the
relational search over previously ingested jobs.

**Query parameters**

| Parameter     | Type    | Description                                                          |
| ------------- | ------- | -------------------------------------------------------------------- |
| `query`       | string  | Free-text search (title, skill, company); max 200                    |
| `location`    | string  | Location scope (e.g. `Bengaluru`)                                    |
| `remote`      | boolean | `true` filters to work-from-home listings                            |
| `salary_min`  | number  | Minimum salary floor                                                 |
| `salary_max`  | number  | Maximum salary ceiling                                               |
| `job_type`    | string  | `full_time` \| `part_time` \| `contract` \| `internship`             |
| `level`       | string  | `entry` \| `mid` \| `senior` \| `lead` \| `executive`                |
| `experience`  | integer | Years of experience                                                  |
| `date_posted` | string  | `today` \| `3days` \| `week` \| `month`                              |
| `company`     | string  | When supplied, also queries Greenhouse/Ashby boards for that company |
| `sort`        | string  | `relevance` (default) \| `recent` \| `salary_desc` \| `salary_asc`  |
| `page`        | integer | 1-based page (default 1)                                             |
| `page_size`   | integer | Items per page, 1–50 (default 20)                                    |

**Response 200** — `JobList` (same shape as `GET /jobs`; items carry the
`source` of the provider that won deduplication).

**Errors**
- `429` — SerpApi monthly search quota exhausted (free plan ~250 searches/month).
- `502` — an upstream provider request failed.

### `GET /jobs/details` — job detail by UUID or external id

No auth required. Resolves a job by its database UUID or by any provider's
external job id (SerpApi `job_id`, USAJobs `PositionID`, etc.). Does **not**
increment views (use `GET /jobs/{job_id}` for that).

### `GET /jobs/salary` — salary data for a job title (OpenWebNinja)

No auth required. Proxy to OpenWebNinja's job-salary endpoint, authenticated
server-side with the same `JSEARCH_API_KEY` (the key never leaves the backend).
Responses are cached for the search TTL.

| Parameter  | Type   | Description                                  |
| ---------- | ------ | -------------------------------------------- |
| `job_title`| string | Job title, e.g. `nodejs developer`           |
| `location` | string | Optional city/country, e.g. `New York`       |

**Response 200** — `{"provider": "openwebninja", "cached": bool, "data": {...}}`.
`data` is the upstream payload. **Errors:** `503` when `JSEARCH_API_KEY` is not
configured; `502` when the upstream request fails.

### `GET /jobs/autocomplete` — web-search autocomplete (OpenWebNinja)

No auth required. Proxy to OpenWebNinja's web-search autocomplete endpoint,
authenticated server-side with `JSEARCH_API_KEY`, cached for the search TTL.

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| `query`   | string | Partial query to complete, e.g. `to`     |

**Response 200** — `{"provider": "openwebninja", "cached": bool, "data": {...}}`.
Same error contract as `/jobs/salary`.

### `GET /jobs/public` — live keyless feeds (Greenhouse + Ashby + Remote OK)

No auth required and **no API keys** on any side. Returns fresh postings from
the three keyless public sources, each normalized to the `JobOut` shape (with a
synthetic `id` of `source:external_id`) and capped at 20 per provider. Failures
are isolated per provider (a broken board yields an empty list, never an error).

| Parameter   | Type   | Description                                  |
| ----------- | ------ | -------------------------------------------- |
| `greenhouse`| string | Company board slug to fetch (default `stripe`) |
| `ashby`     | string | Company hosted page name (default `openai`)  |

**Response 200** — `{"greenhouse": [...], "ashby": [...], "remoteok": [...]}`

**Query parameters**

| Parameter | Type   | Description                                        |
| --------- | ------ | -------------------------------------------------- |
| `id`      | string | Job UUID or SerpApi external job id (max 255)      |

**Response 200** — `JobOut`.

**Errors:** `404` if the job is not found.

### Developer API Dashboard (admin)

| Endpoint                 | Auth   | Description                                        |
| ------------------------ | ------ | -------------------------------------------------- |
| `GET /usage`             | Admin  | Searches used this month, monthly limit, remaining, cache hit rate, cache stats, provider health, last 20 searches |
| `GET /cache-stats`       | Admin  | Cache backend, entries, hits, misses, hit rate     |
| `GET /health`            | Public | `{status, provider, provider_configured}`          |

**`GET /usage` response 200**

```json
{
  "searches_used": 12,
  "monthly_limit": 250,
  "remaining": 238,
  "cache_hit_rate": 40.0,
  "total_requests": 20,
  "cache": { "backend": "memory", "hits": 8, "misses": 12, "entries": 5, "hit_rate": 40.0 },
  "provider": { "name": "serpapi", "configured": true },
  "recent_searches": [
    {
      "endpoint": "/jobs/search",
      "query": "Flutter Developer",
      "location": "Bengaluru",
      "page": 1,
      "response_time_ms": 842,
      "cached": false,
      "status_code": 200,
      "timestamp": "2026-08-15T10:30:00+00:00"
    }
  ]
}
```

Every `/jobs/search` call writes an `api_logs` row (endpoint, query, location,
page, response time, `cached` flag, status code). Only non-cached searches
consume SerpApi quota.

---

## 5. Companies endpoints

### `GET /companies` — list companies

No auth required. `search` (substring on name) and `limit` (1–100, default 24).
Ordered by `verified` first, then `review_count`. Each item includes an
`open_positions` count of active jobs.

**Response 200**

```json
[
  {
    "id": "3c9d1b77-...",
    "name": "Nova Labs",
    "slug": "nova-labs",
    "logo": "https://cdn.example.com/nova.png",
    "website": "https://novalabs.example",
    "industry": "SaaS",
    "description": "Cloud-native SaaS platform for analytics.",
    "location": "Bengaluru, India",
    "size": "51-200",
    "rating": 4.6,
    "review_count": 87,
    "verified": true,
    "created_at": "2026-06-01T08:00:00Z",
    "open_positions": 12
  }
]
```

### `GET /companies/featured` — featured companies

No auth required. `limit` 1–30 (default 6). Companies with active jobs, ordered by
open job count descending.

**Response 200** — array of `CompanyOut`.

### `GET /companies/{slug}` — company detail

No auth required. Returns a single `CompanyOut` with `open_positions`.

**Errors:** `404` if no company matches the slug.

### `POST /companies` — create company

**Admin required.** Body is `CompanyCreate` (`name`, `slug`, optional `logo`,
`website`, `industry`, `description`, `location`, `size`, `rating`, `verified`).
Returns 201 with `CompanyOut`.

### `PATCH /companies/{slug}` — update company

**Admin required.** Body is `CompanyUpdate` (all fields optional). Only supplied
fields are updated.

### `DELETE /companies/{slug}` — delete company

**Admin required.** Returns 204.

---

## 6. Users endpoints

All endpoints below are **Auth required**.

### `GET /users/me` — profile

Returns the `UserOut` of the authenticated user.

### `PATCH /users/me` — update profile

Body is `UserUpdate` (all optional): `name`, `avatar`, `headline`, `bio`, `skills`
(list of strings), `experience`, `location`, `preferences`.

**Response 200** — `UserOut`.

### `PATCH /users/me/preferences` — replace preferences

Body is `PreferencesUpdate`:

```json
{
  "remote_only": true,
  "job_types": ["full_time"],
  "locations": ["Bengaluru"],
  "keywords": ["React", "FastAPI"]
}
```

Replaces the whole `preferences` object.

**Response 200** — `UserOut`.

### `GET /users/me/saved-jobs` — saved jobs

Returns active jobs the user saved, newest-saved first.

**Response 200** — array of `JobOut`.

### `GET /users/me/applications` — application tracker

`status_filter` optionally filters by status (`applied`, `interviewing`, `offered`,
`rejected`, `withdrawn`). Ordered by `applied_at` descending.

**Response 200**

```json
[
  {
    "id": "a1b2c3d4-...",
    "job_id": "e8b4f2a1-...",
    "company_name": "Nova Labs",
    "role": "Software Engineer",
    "status": "interviewing",
    "applied_url": "https://www.linkedin.com/jobs/view/123456",
    "notes": "Phone screen scheduled",
    "applied_at": "2026-08-12T09:00:00Z"
  }
]
```

### `POST /users/me/applications` — log an application

Body is `ApplicationCreate` (all optional except at least one useful field):
`job_id`, `company_name`, `role`, `applied_url`, `status` (default `applied`).
Returns 201 with `ApplicationOut`.

### `PATCH /users/me/applications/{app_id}` — update status/notes

Body is `ApplicationStatusUpdate`:

```json
{ "status": "offered", "notes": "Signed offer" }
```

`notes` is optional and only applied when non-null.

**Errors:** `404` if the application is not found or does not belong to the user.

### `DELETE /users/me/applications/{app_id}` — delete an application

Returns 204. **Errors:** `404` if not found / not owned.

### `GET /users/me/searches` — recent searches

`limit` 1–50 (default 10), newest first.

**Response 200**

```json
[
  {
    "id": "f0e1d2c3-...",
    "query": "flutter developer",
    "filters": { "remote": true },
    "result_count": 0,
    "created_at": "2026-08-13T14:22:00Z"
  }
]
```

---

## 7. Resume / AI tools endpoints

The AI service uses an OpenAI-compatible chat-completions endpoint
(`OPENAI_BASE_URL` + `AI_MODEL`, or a Llama-compatible `LLAMA_BASE_URL`) when
configured, and otherwise falls back to a deterministic heuristic engine — so the
endpoints work without any API key.

### `POST /resume/analyze` — analyze resume text

**Auth required.** Body is `ResumeAnalyzeRequest`:

```json
{
  "resume_text": "Full resume text... (50–100,000 chars)",
  "target_role": "backend",
  "job_description": "Optional job posting text"
}
```

The result is stored in the user's analysis history.

**Response 200**

```json
{
  "ats_score": 78,
  "missing_keywords": ["TypeScript", "Docker"],
  "suggestions": ["Add quantified achievements with percentages or metrics."],
  "summary": "Your resume scored 78/99. Strengthen keyword coverage and quantify impact to reach the top band."
}
```

### `POST /resume/analyze/upload` — analyze an uploaded file

**Auth required.** Multipart form field `file` (UTF-8 text file, max 2 MB).

**Response 200** — same `ResumeAnalysisOut` shape.

**Errors:** `413` if the file exceeds 2 MB, `400` if it is not UTF-8 text.

### `POST /resume/cover-letter` — generate a cover letter

No auth required. Body is `CoverLetterRequest`:

```json
{
  "resume_text": "...",
  "job_title": "Senior Backend Engineer",
  "company_name": "Nova Labs",
  "job_description": "Optional"
}
```

**Response 200**

```json
{ "cover_letter": "Dear Hiring Manager at Nova Labs,..." }
```

### `POST /resume/skill-gap` — compare skills to a role

No auth required. Body is `SkillGapRequest` (`resume_text`, `target_role`).

**Response 200**

```json
{
  "current_skills": ["Python", "FastAPI", "SQL"],
  "missing_skills": ["Docker", "Kubernetes"],
  "recommended_learning": ["Complete a guided project using Docker and add it to your resume."]
}
```

### `POST /resume/interview-prep` — generate interview questions

No auth required. Body is `InterviewPrepRequest` (`job_title`, optional
`job_description`, optional `resume_text`). The question list is adapted when the
description mentions "system design" or "leadership".

**Response 200**

```json
{
  "questions": [
    "Walk me through your experience relevant to this Senior Backend Engineer role.",
    "Describe a challenging project you shipped. What was your role and the outcome?"
  ]
}
```

### `GET /resume/history` — past analyses

**Auth required.** Returns all of the user's saved analyses, newest first.

**Response 200** — array of `ResumeAnalysisOut` (only `ats_score`,
`missing_keywords`, `suggestions`, `summary`).

---

## 8. Notifications endpoints

All endpoints below are **Auth required**.

### `GET /notifications` — list notifications

`unread_only` (`true`/`false`) and `limit` (1–200, default 50). Newest first.

**Response 200**

```json
[
  {
    "id": "9a8b7c6d-...",
    "title": "New jobs for 'flutter developer'",
    "body": "Your saved search 'flutter developer' has new opportunities.",
    "data": { "alert_id": "6f5e4d3c-...", "query": "flutter developer" },
    "read": false,
    "created_at": "2026-08-14T08:00:00Z"
  }
]
```

### `POST /notifications/{notification_id}/read` — mark one read

Returns the updated `NotificationOut`.

**Errors:** `404` if not found or not owned.

### `POST /notifications/read-all` — mark all read

Returns 204.

### `POST /notifications/alerts` — create a job alert

Body is `AlertCreate`:

```json
{
  "query": "flutter developer",
  "filters": { "remote": true },
  "frequency": "daily"
}
```

`frequency` is `instant` | `daily` | `weekly` (default `daily`). Returns 201 with
`AlertOut`.

### `GET /notifications/alerts` — list alerts

Newest first. Returns an array of `AlertOut` (`id`, `query`, `filters`,
`frequency`, `active`, `created_at`).

### `DELETE /notifications/alerts/{alert_id}` — delete an alert

Returns 204. **Errors:** `404` if not found or not owned.

### `POST /notifications/device-token` — register FCM token

Body is `DeviceTokenCreate`:

```json
{ "token": "fcm-registration-token...", "platform": "android" }
```

`platform` is `android` | `ios` | `web` (default `android`). Returns 201.

**Response 201**

```json
{ "registered": true }
```

---

## 9. Admin endpoints

All endpoints below are **Admin required** (the user's `role` must be `admin`,
otherwise `403`).

### `GET /admin/analytics` — platform analytics

Returns headline counts plus popular companies and jobs-per-source distribution.

**Response 200**

```json
{
  "active_users": 482,
  "total_jobs": 12400,
  "total_searches": 9311,
  "total_saved_jobs": 2290,
  "total_applications": 1104,
  "popular_companies": [{ "name": "Nova Labs", "count": 42 }],
  "jobs_by_source": [{ "source": "linkedin", "count": 3100 }]
}
```

### `GET /admin/users` — list users

`limit` (default 100), newest first. Returns an array of `UserOut`.

### `PATCH /admin/users/{user_id}/role` — change role

Query parameter `role` must be `user` or `admin`.

**Errors:** `400` for an invalid role, `404` if the user does not exist.

### `POST /admin/jobs` — manually create a job

Body is `JobCreate` (same fields as `JobOut`, with `source` required). Returns 201
with `JobOut`.

### `PATCH /admin/jobs/{job_id}/moderate` — activate/deactivate

Query parameter `active` (`true`/`false`). Inactive jobs are hidden from search and
detail pages. Returns the updated `JobOut`.

### `POST /admin/companies` — create a company

Body is `CompanyCreate`. Returns 201 with `{"created": true}`.

### `POST /admin/broadcast` — broadcast a notification

Query parameters: `title` (required), `body` (optional). Creates a notification row
for every user. Returns 201.

**Response 201**

```json
{ "sent": 482 }
```

---

## 10. Schemas

### `JobOut` (also used inside `JobList.items`)

```json
{
  "id": "uuid",
  "source": "linkedin|indeed|naukri|internshala|wellfound|company|manual",
  "title": "string",
  "description": "string|null",
  "company_id": "uuid|null",
  "company_name": "string",
  "company_logo": "string|null",
  "location": "string|null",
  "remote": "boolean",
  "salary_min": "number|null",
  "salary_max": "number|null",
  "salary_currency": "string",
  "salary_text": "string|null",
  "job_type": "full_time|part_time|contract|internship|freelance",
  "level": "entry|mid|senior|lead|executive",
  "skills": ["string"],
  "apply_url": "string",
  "apply_on": "string",
  "experience_min": "integer",
  "experience_max": "integer",
  "posted_at": "datetime|null",
  "sponsored": "boolean",
  "views": "integer"
}
```

### `UserOut`

```json
{
  "id": "uuid",
  "name": "string",
  "email": "email",
  "avatar": "string|null",
  "headline": "string|null",
  "bio": "string|null",
  "skills": ["string"],
  "experience": "integer",
  "location": "string|null",
  "resume_url": "string|null",
  "preferences": {
    "remote_only": "boolean",
    "job_types": ["string"],
    "locations": ["string"],
    "keywords": ["string"]
  },
  "role": "user|admin",
  "created_at": "datetime"
}
```

### `TokenPair`

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer"
}
```

---

## 11. End-to-end curl example

The full journey: register → login → search → save a job → list saved jobs → log an
application → refresh tokens.

```bash
API="http://localhost:8000/api/v1"

# 1. Register (returns a token pair directly)
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","password":"supersecret123"}'
# → {"access_token":"...","refresh_token":"...","token_type":"bearer"}

# 2. Login (or re-login)
curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"supersecret123"}' \
  | jq -r .access_token > /tmp/access.txt

TOKEN=$(cat /tmp/access.txt)
AUTH="Authorization: Bearer $TOKEN"

# 3. Search jobs (remote backend roles)
curl -s "$API/jobs?q=backend&remote=true&sort=recent&page=1&page_size=5" \
  -H "$AUTH"
# → {"total":N,"page":1,"page_size":5,"items":[...]}

# 4. Save the first job (grab its id from the search response)
JOB_ID="e8b4f2a1-0000-0000-0000-000000000000"
curl -s -X POST "$API/jobs/$JOB_ID/save" -H "$AUTH"
# → {"saved":true}

# 5. List saved jobs
curl -s "$API/users/me/saved-jobs" -H "$AUTH"

# 6. Log an application
curl -s -X POST "$API/users/me/applications" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"job_id\":\"$JOB_ID\",\"status\":\"applied\",\"notes\":\"applied via LinkedIn\"}"
# → {"id":"...","job_id":"...","company_name":null,"role":null,
#    "status":"applied","applied_url":null,"notes":"applied via LinkedIn","applied_at":"..."}

# 7. Update its status
APP_ID="a1b2c3d4-0000-0000-0000-000000000000"
curl -s -X PATCH "$API/users/me/applications/$APP_ID" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"status":"interviewing","notes":"phone screen Friday"}'

# 8. Refresh the token pair before the access token expires
curl -s -X POST "$API/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$(cat /tmp/refresh.txt)\"}"
# → new access_token + refresh_token; replace both stored values
```

> Tip: pipe responses through `jq` to extract tokens/ids. `POST /auth/logout` is a
> 204 with no body, so pass `-o /dev/null -w "%{http_code}"` to verify.