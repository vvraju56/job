# Makeable Jobs — Job Aggregation System

This document explains how the aggregation system ingests job listings from
multiple sources and how to add a new source adapter.

---

## 1. Overview

```
 source (LinkedIn / Indeed / Naukri / Internshala / Wellfound / Company)
        │
        ▼  fetch_latest() → NormalizedJob[]
 aggregator.run_ingestion()
        │
        ▼  upsert (dedupe by source + external_id)
 Supabase PostgreSQL jobs table
```

The pipeline runs on a schedule via **Celery beat** (`ingest-jobs-hourly`, every
hour at `:15`), calling `app.workers.tasks.ingest_jobs`, which wraps
`run_ingestion`. It can also be run ad hoc from the CLI/seed script.

Key principle: **Makeable redirects, it doesn't republish.** Adapters resolve
public listing metadata and the canonical `apply_url`; full copyrighted job
descriptions are never scraped into the platform.

---

## 2. Files involved

| File                                   | Role                                            |
| -------------------------------------- | ----------------------------------------------- |
| `backend/app/adapters/base.py`         | `NormalizedJob` dataclass + `BaseAdapter` ABC   |
| `backend/app/adapters/sources.py`      | Concrete adapters (one per source)              |
| `backend/app/adapters/aggregator.py`   | Adapter registry + `run_ingestion` + `upsert_jobs` |
| `backend/app/services/providers/base.py`   | `JobProvider` ABC — **search-time** provider contract (SerpApi, LinkedIn, etc.) |
| `backend/app/services/providers/serpapi.py` | SerpApi Google Jobs provider (default)          |
| `backend/app/services/providers/__init__.py` | Provider registry (`PROVIDERS`, `get_provider`) |
| `backend/app/services/jobs_service.py` | Search orchestration: cache → usage log → provider → upsert |
| `backend/app/services/cache.py`        | Redis cache (6h TTL) with in-memory fallback    |
| `backend/app/workers/celery_app.py`    | Scheduled `ingest_jobs` task                    |
| `backend/scripts/seed.py`              | One-off seeding for local/dev DB                |

> The ingestion adapters (`BaseAdapter`) fill the DB in the background; the
> search providers (`JobProvider`) answer live `GET /jobs/search` requests and
> persist their results with `source='serpapi'`. Both produce `NormalizedJob`
> records, so ingestion and live search share the same persistence path.

---

## 3. The contract: `NormalizedJob` + `BaseAdapter`

Every source must produce a `NormalizedJob` — a canonical, source-agnostic record
(`backend/app/adapters/base.py`):

```python
@dataclass
class NormalizedJob:
    source: str
    external_id: str
    title: str
    company_name: str
    location: str | None = None
    remote: bool = False
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "INR"
    salary_text: str | None = None
    job_type: str = "full_time"       # full_time|part_time|contract|internship|freelance
    level: str = "entry"              # entry|mid|senior|lead|executive
    skills: list[str] = []
    description: str | None = None
    apply_url: str = ""               # canonical URL on the original portal
    apply_on: str = "Original Website"
    experience_min: int = 0
    experience_max: int = 0
    posted_at: datetime = <now UTC>
    company_logo: str | None = None
```

And the adapter contract:

```python
class BaseAdapter(ABC):
    source_name: str = "base"

    @abstractmethod
    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        """Fetch and normalize recent listings from the source."""
        raise NotImplementedError

    async def search(self, query: str, limit: int = 20) -> list[NormalizedJob]:
        """Default search: fetch latest and filter locally (override per source)."""
        ...
```

---

## 4. Normalization & deduplication

### 4.1 Upsert logic

`aggregator.upsert_jobs` inserts only **new** jobs. Dedupe key is the composite
**(source, external_id)**:

```python
async def upsert_jobs(db: AsyncSession, jobs: list[NormalizedJob]) -> int:
    count = 0
    for item in jobs:
        existing = await db.execute(
            select(Job).where(Job.external_id == item.external_id, Job.source == item.source)
        ).scalar_one_or_none()
        if existing is not None:
            continue                      # already ingested → skip
        db.add(Job(external_id=..., source=..., ...))
        count += 1
    await db.commit()
    return count
```

Consequences:

- Re-running ingestion is **idempotent** — the same listing is never duplicated.
- Two portals listing the same role are stored as **two separate jobs** (different
  `source`), each pointing at its own canonical `apply_url`.
- A deactivated (`active=false`) job is **re-created** if the source emits the same
  `external_id` again; to keep a job offline, remove it from the source feed or
  pair moderation with content changes.

### 4.2 Failure isolation

`run_ingestion` iterates the registry and isolates each adapter:

```python
for name in names:
    adapter = ADAPTERS.get(name)
    try:
        jobs = await adapter.fetch_latest(limit=limit)
        count = await upsert_jobs(db, jobs)
    except Exception as exc:
        logger.exception("Adapter %s failed: %s", name, exc)
        results[name] = 0
```

A broken source logs (`Adapter <name> failed: ...`) and reports `0` rather than
aborting the whole batch. Monitor these logs — `GET /admin/analytics`
(`jobs_by_source`) will show a source at 0 when its adapter is failing.

---

## 4.2 Search-time providers (the 6-API aggregator)

In addition to the background ingestion adapters above, live search runs through
the **provider** layer (`backend/app/services/providers/`). A search provider
implements the same `NormalizedJob` output but is invoked **on demand** by
`GET /jobs/search` instead of on a Celery schedule:

| Provider      | Module               | Keyword search? | Key required                       |
| ------------- | -------------------- | --------------- | ---------------------------------- |
| SerpApi       | `providers/serpapi.py`    | yes        | `SERPAPI_API_KEY`                  |
| JSearch       | `providers/jsearch.py`    | yes        | `JSEARCH_API_KEY`                  |
| USAJobs       | `providers/usajobs.py`    | yes        | `USAJOBS_API_KEY` + `USAJOBS_EMAIL`|
| Remote OK     | `providers/remoteok.py`   | yes (local filter) | none                     |
| Greenhouse    | `providers/greenhouse.py` | no (company board)  | none                     |
| Ashby         | `providers/ashby.py`      | no (company board)  | none                     |

`services/aggregator.py` fans out to every provider selected by
`ENABLED_PROVIDERS` (default `serpapi,jsearch,usajobs,remoteok`), applies
universal filters (remote/salary/type/level), then deduplicates across sources:

```python
# Keep the highest-priority source for each unique posting.
SEARCH_PRIORITY = ["serpapi", "jsearch", "greenhouse", "ashby", "usajobs", "remoteok"]
```

Dedup key = `(title, company, location, apply_url)`. Both ingestion adapters and
search providers write through the same `upsert_jobs` path, so a job first seen
by Remote OK and later by SerpApi is deduped by `(source, external_id)` at the
row level and by the priority key at the aggregate level.

---

## 5. Adding a new source adapter

Step-by-step, using a hypothetical "Glassdoor" adapter:

### Step 1 — Create the adapter class

Add a new class to `backend/app/adapters/sources.py`:

```python
class GlassdoorAdapter(BaseAdapter):
    source_name = "glassdoor"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        # Real implementation: official Glassdoor RSS/partner feed.
        jobs = await self._fetch_feed(limit=limit)   # your own feed client
        return [
            NormalizedJob(
                source=self.source_name,
                external_id=item["id"],              # id on the source
                title=item["title"],
                company_name=item["company"],
                location=item["location"],
                remote=item.get("remote", False),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                salary_currency="INR",
                salary_text=item.get("salary_text"),
                job_type=normalize_type(item.get("type")),   # map source values → enum
                level=normalize_level(item.get("seniority")),
                skills=item.get("skills", []),
                description=item.get("summary"),             # metadata only
                apply_url=item["apply_url"],                 # canonical URL
                apply_on="Glassdoor",
                experience_min=item.get("exp_min", 0),
                experience_max=item.get("exp_max", 0),
                posted_at=item.get("posted_at"),
            )
            for item in jobs
        ]
```

### Step 2 — Register the adapter

In `backend/app/adapters/aggregator.py`, import it and add it to the registry:

```python
from app.adapters.sources import (
    CompanyAdapter,
    GlassdoorAdapter,          # new
    IndeedAdapter,
    ...
)

ADAPTERS: dict[str, BaseAdapter] = {
    adapter.source_name: adapter
    for adapter in [
        LinkedinAdapter(),
        IndeedAdapter(),
        NaukriAdapter(),
        InternshalaAdapter(),
        WellfoundAdapter(),
        CompanyAdapter(),
        GlassdoorAdapter(),     # new
    ]
}
```

Registration is driven by `source_name` — nothing else needs to change. Ingestion
will now include `"glassdoor"` in the default source list.

### Step 3 — Extend the enum

The `Job.source` column is a Postgres enum (`job_source` in
`supabase/schema.sql` and `models.py`). Add the new value:

```sql
-- supabase/schema.sql
alter type job_source add value if not exists 'glassdoor';
```

And in `backend/app/models/models.py`:

```python
JOB_SOURCES = ("linkedin", "indeed", "naukri", "internshala", "wellfound", "company", "manual", "glassdoor")
```

Also update the `JobSource` literal in `backend/app/schemas/schemas.py` so
Pydantic validation accepts it.

### Step 4 — Add `apply_on` label

`apply_on` is the human label shown on listing cards ("Apply on Glassdoor"). Set it
in every `NormalizedJob` the adapter emits (see Step 1).

### Step 5 — Test

```bash
cd backend
python -c "import asyncio; from app.adapters.aggregator import run_ingestion; from app.core.database import SessionLocal; \
async def t():\
  async with SessionLocal() as db: print(await run_ingestion(db, sources=['glassdoor'], limit=10))\
asyncio.run(t())"
```

Then confirm the jobs appear via the API:

```bash
curl "http://localhost:8000/api/v1/jobs?source=glassdoor"
```

### Step 6 — Legal check before enabling in production

See §7. Only ship the adapter if the source offers an official feed/API or
explicit opt-in. The checked-in adapters emit **demo listings**; replace them with
real integrations before production.

---

## 6. Adding a new source via admin (no code)

If a role should appear without a new portal adapter, use the manual admin route:

```
POST /api/v1/admin/jobs
```

with `"source": "manual"` and the full `JobCreate` body (see `docs/admin.md` §2).
Manual jobs share the same `jobs` table, search, and save/similar features.

---

## 7. Legal note — do not scrape copyrighted content

Makeable Jobs is a **job aggregator**, not a content republisher. The legal rules
the project follows:

1. **No wholesale scraping of job descriptions.** Adapters normalize *publicly
   available listing metadata* (title, company, location, salary, apply URL) and
   never store full copyrighted postings.
2. **Redirect, don't host.** Every listing's `apply_url` points at the original
   portal; users read the full description and apply there. This is also why the
   base adapter docstring states: *"Adapters never store copyrighted content. They
   resolve public listing metadata and the canonical apply URL so the platform can
   redirect users back to the original portal."*
3. **Prefer official channels.** Use each source's official RSS feed, partner/ATS
   API (Greenhouse, Lever, Ashby), or opt-in listing exports before considering
   any automated collection. Respect `robots.txt`, terms of service, rate limits,
   and DMCA/attribution expectations.
4. **Re-review per source.** API terms change; re-check a source's terms before
   enabling its adapter in production.

If you must display a description, use the source's summary/teaser or a licensed
feed — never copy the full copyrighted text into the `jobs.description` column.

---

## 8. Operations

### 8.1 Scheduled ingestion

Celery beat schedule (in `celery_app.py`):

| Task                       | Schedule          |
| -------------------------- | ----------------- |
| `ingest_jobs`              | hourly at `:15`   |
| `send_alert_digest`        | daily 08:00 UTC   |

Run worker + beat as separate processes (see `docs/deployment.md` §2.3).

### 8.2 Manual run

```bash
celery -A app.workers.celery_app:celery_app call app.workers.tasks.ingest_jobs --args '[[], 100]'
```

or for one source:

```bash
celery -A app.workers.celery_app:celery_app call app.workers.tasks.ingest_jobs --args '[["linkedin"], 50]'
```

### 8.3 Observability

- Per-source counts are logged (`Ingested N jobs from <source>`).
- `GET /admin/analytics → jobs_by_source` reports live supply per source.
- Watch logs for `Adapter <name> failed: ...` and check the source's feed health
  if a source stays at 0.