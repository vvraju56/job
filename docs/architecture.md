# Makeable Jobs — Architecture Notes

> One Search. Every Opportunity.

Makeable Jobs is a **job aggregation platform**: it indexes job listings from
multiple portals (LinkedIn, Indeed, Naukri, Internshala, Wellfound, company career
pages) and redirects users to the **original application page**. It never owns or
copies the jobs — every listing points to the canonical external URL
(`apply_on: "Original Website"`).

---

## 1. Monorepo layout

```
.
├── web/            # Next.js 15 website (React 19, TS, Tailwind, Framer Motion)
├── mobile/         # Flutter app (Riverpod, GoRouter, Dio, FCM) for Android/iOS
├── backend/        # FastAPI REST API
│   └── app/
│       ├── main.py             # entrypoint, CORS, rate limiting, router wiring
│       ├── api/
│       │   ├── deps.py         # current-user / admin guards, DB dependency
│       │   └── routes/         # auth, jobs, serpapi (live search+usage), companies, users, resume, notifications, admin
│       ├── adapters/           # base.py, sources.py, aggregator.py (job ingestion)
│       ├── core/               # config, database, security (JWT/bcrypt)
│       ├── models/             # SQLAlchemy ORM models (incl. ApiLog)
│       ├── schemas/            # Pydantic request/response schemas
│       ├── services/           # ai_service.py, cache.py, jobs_service.py, providers/ (base + serpapi)
│       └── workers/            # celery_app.py (ingestion, alert digest, push)
├── supabase/       # schema.sql — tables, enums, indexes, RLS, storage bucket
├── public/         # optional static site (served by Cloudflare Workers)
└── docs/           # this documentation
```

## 2. Tech stack

| Layer         | Technology                                                   |
| ------------- | ------------------------------------------------------------ |
| Website       | Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion |
| Mobile        | Flutter, Riverpod, GoRouter, Dio, Firebase Messaging, SharedPreferences |
| Backend       | Python 3, FastAPI, SQLAlchemy 2 (async), Pydantic v2, Uvicorn |
| Workers       | Celery + Redis (beat scheduler)                              |
| Database      | Supabase PostgreSQL (asyncpg driver)                         |
| Storage       | Supabase Storage (private `resumes` bucket)                  |
| Auth          | JWT (HS256) + bcrypt; Supabase providers Email/Google/GitHub/LinkedIn |
| AI            | OpenAI-compatible chat completions with heuristic fallback   |
| Notifications | Firebase Cloud Messaging + in-app notifications              |
| Job search     | 6-provider aggregation: SerpApi Google Jobs + USAJobs + JSearch + Remote OK (+ Greenhouse/Ashby ATS boards) |
| Cache          | Redis (`REDIS_URL`) with in-memory TTL fallback; 6h job-search TTL       |
| Rate limiting | slowapi (200 req/min per IP)                                 |
| Deploy        | Vercel (web), Railway/Render (backend), Supabase, Cloudflare Workers |

---

## 3. System design — data flow

```
                ┌─────────────────────────────────────────────────────┐
                │                   SOURCE ADAPTERS                    │
                │  LinkedIn · Indeed · Naukri · Internshala ·          │
                │  Wellfound · Company career pages                    │
                └───────────────────────┬─────────────────────────────┘
                                        │  fetch_latest() → NormalizedJob[]
                                        ▼
                ┌─────────────────────────────────────────────────────┐
                │                 aggregator.run_ingestion            │
                │  (Celery beat, hourly) — upsert by (source, external_id) │
                └───────────────────────┬─────────────────────────────┘
                                        ▼
                ┌─────────────────────────────────────────────────────┐
                │          Supabase PostgreSQL  (jobs table)          │
                │  GIN full-text index + btree indexes for filters    │
                └──────────┬──────────────────────┬──────────────────┘
                           │  GET /api/v1/jobs    │  SELECT …
                           ▼                      ▼
                ┌────────────────────────┐   ┌──────────────────────────┐
                │   Next.js website      │   │   Flutter mobile app     │
                │   (Vercel, SSR)        │   │   (Dio, JWT bearer)      │
                └──────────┬─────────────┘   └────────────┬─────────────┘
                           │  redirect                    │  redirect
                           ▼                              ▼
                ┌─────────────────────────────────────────────────────┐
                │   ORIGINAL PORTAL  (LinkedIn/Indeed/... apply_url)  │
                └─────────────────────────────────────────────────────┘

   Auth: register/login → JWT pair → Bearer header on protected routes
   AI:   /resume/* → ai_service → OpenAI (or heuristic fallback)
   Push: Celery digest → notifications table + FCM → device tokens
```

### Request path (example: search → save → apply)

1. Client calls `GET /api/v1/jobs?q=flutter&remote=true`.
2. FastAPI builds a SQLAlchemy query, applies filters/sort/pagination, returns
   `JobList` with `total/page/page_size/items`.
3. Authenticated user saves via `POST /api/v1/jobs/{id}/save` (idempotent;
   unique `(user_id, job_id)`).
4. The client renders `apply_url` and opens the **original portal** in the browser
   (`url_launcher` on mobile) — Makeable never hosts the application form.

---

## 4. Database schema overview

Eleven tables defined in `supabase/schema.sql` (mirrored by SQLAlchemy models):

| Table              | Purpose                                              | Key columns / notes                          |
| ------------------ | ---------------------------------------------------- | -------------------------------------------- |
| `profiles`         | Users (extends `auth.users`)                          | `role` enum `user\|admin`, JSON `skills`, `preferences` |
| `companies`        | Company profiles                                     | `slug` unique, `verified`, `rating`, `review_count` |
| `jobs`             | Normalized job listings                              | `external_id`+`source` dedupe key, GIN tsvector index, `active` flag |
| `saved_jobs`       | User's saved jobs                                    | unique `(user_id, job_id)`                   |
| `applications`     | Application tracker                                  | `status` enum, notes, applied_url            |
| `searches`         | Search history (recent searches)                     | `query`, JSON `filters`                      |
| `notifications`    | In-app notifications                                 | `channel` enum `push\|email`, `read` flag    |
| `alerts`           | User-created job alerts                              | `frequency` (`instant`/`daily`/`weekly`), `active` |
| `device_tokens`    | FCM registration tokens per user                     | unique `(user_id, token)`, `platform`        |
| `resume_analyses`  | Saved AI resume analyses                             | `ats_score`, JSON `missing_keywords`/`suggestions`/`raw` |
| `api_logs`         | SerpApi/developer usage log                          | `endpoint`, `query`, `location`, `cached`, `status_code`, `created_at` |

**Enums:** `job_source` (incl. `serpapi`), `job_type`, `employment_level`,
`application_status`, `notification_channel`, `role`.

**Indexes** (from `schema.sql`):

```sql
idx_jobs_search   → GIN (to_tsvector('english', title || company_name || description))
idx_jobs_location → (location)
idx_jobs_remote   → (remote)
idx_jobs_active   → (active, posted_at desc)
idx_jobs_source   → (source)
idx_jobs_company  → (company_id)
idx_applications_user → (user_id, status)
idx_searches_user → (user_id, created_at desc)
idx_notifications_user → (user_id, read, created_at desc)
```

**Triggers:** `handle_new_user()` creates a `profiles` row on `auth.users` insert;
`set_updated_at()` maintains `updated_at` on profiles/jobs.

**RLS:** every table has row-level security. `companies`/`jobs` are public-read;
all user-owned tables restrict access to `auth.uid()`. The backend uses the
service role key (bypasses RLS); policies are defense-in-depth for direct clients.

---

## 5. Job aggregation design

### 5.1 Adapter pattern

Each source implements a `BaseAdapter` (in `backend/app/adapters/base.py`) with a
single contract method:

```python
class BaseAdapter(ABC):
    source_name: str = "base"

    @abstractmethod
    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]: ...
```

Every adapter returns **`NormalizedJob`** — a canonical, source-agnostic dataclass
(`source`, `external_id`, `title`, `company_name`, location, salary, type, level,
skills, `apply_url`, experience range, timestamps).

Concrete adapters: `LinkedinAdapter`, `IndeedAdapter`, `NaukriAdapter`,
`InternshalaAdapter`, `WellfoundAdapter`, `CompanyAdapter`. The checked-in
implementations emit **demo listings** as stubs; production wires each to the
source's official RSS feed, partner API, or careers-page feed (Greenhouse/Lever).

### 5.2 Normalization table

| `NormalizedJob` field | Source example (LinkedIn)      | Stored in `jobs` column |
| --------------------- | ------------------------------ | ----------------------- |
| `source`              | `"linkedin"`                   | `source` (enum)         |
| `external_id`         | listing id on the portal       | `external_id`           |
| `title`               | `"Software Engineer"`          | `title`                 |
| `company_name`        | `"Nova Labs"`                  | `company_name`          |
| `location`            | `"Bengaluru, India"`           | `location`              |
| `remote`              | `true/false`                   | `remote` (bool)         |
| `salary_min/max`      | `1200000 / 2400000`            | `salary_min/max` (Numeric) |
| `salary_currency`     | `"INR"`                        | `salary_currency`       |
| `salary_text`         | `"₹12L – ₹24L/yr"`             | `salary_text`           |
| `job_type`            | `"full_time"`                  | `job_type` (enum)       |
| `level`               | `"mid"`                        | `level` (enum)          |
| `skills`              | `["TypeScript", "React"]`      | `skills` (JSONB)        |
| `description`         | listing body                   | `description`           |
| `apply_url`           | canonical job URL on portal    | `apply_url`             |
| `apply_on`            | `"LinkedIn"`                   | `apply_on`              |
| `experience_min/max`  | `2 / 6`                        | `experience_min/max`    |
| `posted_at`           | feed timestamp                 | `posted_at`             |

### 5.3 Upsert & deduplication

`aggregator.upsert_jobs` dedupes by the composite key **(source, external_id)**:
if a `Job` already exists with the same `external_id` and `source`, it is skipped;
otherwise a new row is inserted. Because adapters are idempotent and Celery runs
ingestion hourly, the same listing is never duplicated across runs.

```python
existing = await db.execute(
    select(Job).where(Job.external_id == item.external_id, Job.source == item.source)
).scalar_one_or_none()
if existing is not None:
    continue
```

`run_ingestion` iterates the adapter registry, isolates each adapter in its own
try/except (a failing source logs and reports 0 rather than aborting the batch),
and returns per-source counts.

### 5.4 Legal note

**Makeable Jobs does not scrape copyrighted job descriptions.** Adapters normalize
publicly available listing *metadata* and resolve the canonical `apply_url`, so
the platform redirects users back to the original portal to read the full posting
and apply. This is stated in the adapter docstrings, the README, and the base
adapter contract: *"Adapters never store copyrighted content."* When building a
real adapter, use official RSS feeds, partner APIs, or opt-in/ATS exports — never
scrape content that the source does not license for redistribution.

### 5.5 Live search provider aggregation (6 APIs)

The web and Flutter apps search through `GET /jobs/search`, which the backend
serves by fanning out to **every enabled provider** concurrently rather than a
single upstream:

```
Client ──► GET /jobs/search ──► services/aggregator.search_aggregated
                                       │
        ┌──────────────────────────────┼───────────────────────────────┐
        ▼                              ▼                                ▼
  1. Redis cache                2. api_logs                       3. providers
     (md5(query|location|         (usage + cache-hit              SerpApi · USAJobs
      page|filters|providers),    tracking)                       JSearch · Remote OK
      6h)                             │                            (keyword search)
        │                              ▼                            Greenhouse/Ashby
        ▼                       quota check (< monthly            (join on `company`)
   return cached ids ──┐       limit, else 429)
                       │              │                                │
                       ▼              ▼                                ▼
                       └──────────► merge → dedupe → upsert_jobs (source=provider,
                                   external_id=provider job id)  → cache ids → JobList
```

Key properties:

- **Provider adapter pattern** (`backend/app/services/providers/`): `JobProvider`
  ABC in `base.py`; concrete providers `serpapi.py`, `usajobs.py`, `jsearch.py`,
  `greenhouse.py`, `ashby.py`, `remoteok.py`; registry in `providers/__init__.py`.
  `ENABLED_PROVIDERS` (comma-separated) selects which ones the aggregator calls.
  Greenhouse/Ashby set `supports_query_search=False` — they are company-board
  ATS sources that join only when a `company` filter is supplied. Future
  upstreams (LinkedIn partner API, Indeed official integrations, Lever, Workday,
  BambooHR, SmartRecruiters) implement the same interface.
- **Concurrency**: providers run with `asyncio.gather`; a failing provider
  contributes nothing rather than aborting the search (failure isolation).
- **Deduplication** across sources: same (title, company, location, apply URL)
  keeps the highest-priority source — SerpApi > JSearch > Greenhouse > Ashby >
  USAJobs > Remote OK (`SEARCH_PRIORITY`).
- **Caching** (`services/cache.py`): Redis-backed with an in-process TTL
  fallback. A search key = SHA-256 of `(query, location, page, filters,
  providers)`; the cached payload is the persisted job UUIDs. TTL default 6
  hours (`SERPAPI_CACHE_TTL_HOURS`). Cache hits never consume provider quota.
- **Quota guard**: only non-cached searches count toward the SerpApi monthly
  budget (`SERPAPI_MONTHLY_LIMIT`, default 250). Reaching the limit returns 429.
- **Persistence**: results are upserted into `jobs` with `source=<provider>`
  keyed by the provider's external id, so saved jobs, similar jobs, `/jobs/{id}`
  details, trending and recommendations all keep working unchanged.
- **Fallback**: with **no** provider configured the endpoint serves the
  relational search over previously ingested jobs (keeps local dev functional).
- **Usage tracking**: every search writes an `api_logs` row; `GET /usage`
  (admin) powers the Developer API Dashboard at `/developers`.

---

## 6. Search engine approach

Search is **database-driven** — there is no separate Elasticsearch/Solr service.

1. **Full-text index:** `idx_jobs_search` is a GIN index over a `to_tsvector` of
   `title + company_name + description`. Although the current `GET /jobs` handler
   applies `ILIKE` filters (see below), the index exists to support fast ranked
   full-text queries and can be adopted with `websearch_to_tsquery` when the corpus
   grows.
2. **Filter pipeline:** `_apply_filters` in `jobs.py` progressively narrows the
   `SELECT` statement using `ILIKE` substring matches (`q`, `location`, `company`),
   boolean equality (`remote`), and numeric overlap windows for salary/experience
   ranges:
   - `salary_min`: `Job.salary_max >= salary_min`
   - `salary_max`: `Job.salary_min <= salary_max`
   - same overlap logic for `experience_min/max`.
3. **Sorting:** `recent` (posted_at desc), `salary_desc` / `salary_asc`
   (nulls-last), and `relevance` (title match ranks first, then recency) — only
   meaningful when `q` is provided.
4. **Pagination:** `page`/`page_size` with a `COUNT(*)` subquery for `total`.
5. **In-app filtering:** the Flutter/Next.js clients issue targeted queries per
   facet (remote, job_type, level, source), reusing the same filters. Only active
   jobs (`active = true`) are ever returned.

**Trending** is computed as `ORDER BY views DESC`; **search suggestions** come from
`GROUP BY title ORDER BY count(*) DESC` over matching titles; **similar jobs** match
on the last token of the job title.

---

## 7. AI features design

`backend/app/services/ai_service.py` exposes a thin `AIService` that wraps an
**OpenAI-compatible** `POST {base}/chat/completions` endpoint:

- `OPENAI_API_KEY` + `OPENAI_BASE_URL` (default `https://api.openai.com/v1`) + `AI_MODEL`
- or `LLAMA_BASE_URL` + `LLAMA_MODEL` for a self-hosted Llama endpoint.

When neither is configured (`available == False`), every feature falls back to a
**deterministic heuristic engine** so the platform works keyless:

| Feature            | Endpoint                    | Heuristic fallback                                    |
| ------------------ | --------------------------- | ----------------------------------------------------- |
| Resume analysis    | `POST /resume/analyze`      | Score = length + keyword-density + action-verbs + metrics, clamped 20–99 |
| Cover letter       | `POST /resume/cover-letter` | Templated letter using extracted skills               |
| Skill gap          | `POST /resume/skill-gap`    | Role map (flutter/react/backend/data/designer) vs. extracted skills |
| Interview prep     | `POST /resume/interview-prep` | Template questions + conditional system-design/leadership questions |

The analyzer scores on: word-count band (10–30), number of recognized skill
keywords (6–30), action verbs (up to 20), and quantification metrics such as `%`
or `₹/K/M` numbers (4–20). Results are stored in `resume_analyses` for history.

---

## 8. Notification pipeline

```
Celery Beat (daily 08:00 UTC, hourly :15)
        │
        ├── ingest_jobs ────────► run_ingestion() ──► jobs table
        │
        └── send_alert_digest ──► for each active Alert
                                        │
                                        ▼
                         notifications table row
                        (title "New jobs for '<query>'", data.alert_id)
                                        │
                                        └──► in-app: GET /api/v1/notifications
                                                  (polled by clients)

    push_alert task ──► fan-out to DeviceToken rows ──► FCM (firebase-admin)
```

- Users create **alerts** (`POST /notifications/alerts`) with `instant|daily|weekly`
  frequency.
- The daily digest materializes a `Notification` row per alert per user.
- A dedicated `push_alert` task (production path) looks up the user's
  `device_tokens` and sends via Firebase Cloud Messaging using the service-account
  credentials (`FIREBASE_CREDENTIALS`).
- Clients register device tokens via `POST /notifications/device-token`.

---

## 9. Security measures

| Area                      | Implementation                                                             |
| ------------------------- | -------------------------------------------------------------------------- |
| Authentication            | JWT (HS256) access/refresh pair; `sub` + `type` claims; 30-min access, 14-day refresh |
| Passwords                 | bcrypt hashing (`bcrypt.hashpw`/`checkpw`)                                 |
| Rate limiting             | slowapi, `Limiter` keyed on remote IP, **200 req/min** default; custom 429 handler |
| Input validation          | Pydantic v2 schemas on every route (types, lengths, enums, email format)   |
| SQL injection             | SQLAlchemy ORM + asyncpg parameterized queries; no string interpolation of user values |
| Authorization             | `CurrentUser` guard (Bearer token → user) and `CurrentAdmin` guard (`role == "admin"` else 403) |
| Row-level security        | Supabase RLS on every table (public read for jobs/companies; owner-only for the rest) |
| Upload safety             | Resume upload capped at 2 MB and restricted to UTF-8 text (`413`/`400`)    |
| CORS                      | Whitelist from `CORS_ORIGINS`; credentials allowed                          |
| Secrets                   | Loaded via `.env` (pydantic-settings); service-role key never shipped to clients |

---

## 10. Performance

- **SSR on the web:** Next.js 15 server-side rendering for public pages (job
  search, job detail, company pages) keeps the client light and helps SEO.
- **Async I/O:** FastAPI + SQLAlchemy async (asyncpg) means the API thread-pool
  isn't blocked on DB I/O.
- **Database caching:** Supabase caches hot reads; GIN/btree indexes keep search
  fast; `active, posted_at desc` index serves the default sort.
- **Rate limiting** prevents abuse; **pool_pre_ping** keeps DB connections fresh.
- **Lazy loading on mobile:** `cached_network_image` for logos, paginated job
  lists, skeleton/loading states via Riverpod providers.
- **Ingestion efficiency:** hourly Celery ingestion with dedupe upserts keeps
  writes minimal (no per-run full rewrites).

---

## 11. SEO strategy

- **Semantic URLs:** jobs are reachable via `GET /jobs/{id}`; companies via
  `/companies/{slug}` (human-readable slug).
- **Server-rendered content:** Next.js SSR/ISR serves the listing content directly
  to crawlers instead of a client-side-only shell.
- **Meta tagging:** per-route title/description/OG tags in the Next.js app
  (`/jobs/{id}` embeds job title, company, location, salary).
- **Structured data:** JSON-LD `JobPosting` markup on detail pages (salaryRange,
  employmentType, hiringOrganization, directApply URL → `apply_url`).
- **Public read API:** jobs/companies are readable without auth, so static
  prerendering and sitemap generation can use `GET /jobs` freely.
- **Redirect model:** because users apply on the original portal, the platform
  sends traffic *out* rather than hoarding it — marketing effort focuses on
  branded search terms ("makeable jobs", aggregator comparisons) and the static
  `public/` site on Cloudflare Workers.