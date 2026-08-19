# Makeable Jobs — Admin Panel Guide

Admin operations are exposed through the `/api/v1/admin/*` routes. Every admin
endpoint requires:

1. A valid access token (`Authorization: Bearer <access_token>`).
2. A user whose `profiles.role == "admin"`. Otherwise the API returns
   **403 Forbidden** (`{"detail": "Admin access required"}`).

The admin guard is `get_current_admin` in `backend/app/api/deps.py`, applied to
every route in `backend/app/api/routes/admin.py` (and to the write routes in
`companies.py`).

---

## 1. Making a user an admin

There is no self-service promotion. Use the admin role endpoint:

```
PATCH /api/v1/admin/users/{user_id}/role?role=admin
```

**Example**

```bash
API="https://<api-host>/api/v1"
ADMIN_TOKEN="<an existing admin's access token>"
TARGET_USER_ID="3c9d1b77-0000-0000-0000-000000000000"

curl -X PATCH "$API/admin/users/$TARGET_USER_ID/role?role=admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response 200**

```json
{
  "id": "3c9d1b77-0000-0000-0000-000000000000",
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "avatar": null,
  "headline": null,
  "bio": null,
  "skills": [],
  "experience": 0,
  "location": null,
  "resume_url": null,
  "preferences": { "remote_only": false, "job_types": [], "locations": [], "keywords": [] },
  "role": "admin",
  "created_at": "2026-07-20T09:12:00Z"
}
```

`role` accepts only `user` or `admin` — anything else returns **400**.
A nonexistent user returns **404**.

> **Bootstrap tip:** `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` exist for the seed
> / first-run script. Alternatively, promote the first account you create from
> `user` to `admin` once you already have an admin token (e.g. by promoting a
> placeholder account during local setup).

---

## 2. All admin endpoints

| Method | Path                            | Auth   | Description                            |
| ------ | ------------------------------- | ------ | -------------------------------------- |
| GET    | `/admin/analytics`              | admin  | Headline metrics + distribution charts |
| GET    | `/admin/users`                  | admin  | List users (newest first)              |
| PATCH  | `/admin/users/{user_id}/role`   | admin  | Promote/demote (`role=user\|admin`)    |
| POST   | `/admin/jobs`                   | admin  | Manually create a job                  |
| PATCH  | `/admin/jobs/{job_id}/moderate` | admin  | Activate/deactivate a job (`active=true\|false`) |
| POST   | `/admin/companies`              | admin  | Manually create a company              |
| POST   | `/admin/broadcast`              | admin  | Send a notification to every user      |

### GET `/admin/analytics`

No parameters. Returns platform-level counts and two distributions used to drive
the dashboard.

```bash
curl "$API/admin/analytics" -H "Authorization: Bearer $ADMIN_TOKEN"
```

```json
{
  "active_users": 482,
  "total_jobs": 12400,
  "total_searches": 9311,
  "total_saved_jobs": 2290,
  "total_applications": 1104,
  "popular_companies": [ { "name": "Nova Labs", "count": 42 } ],
  "jobs_by_source": [ { "source": "linkedin", "count": 3100 } ]
}
```

| Field               | Definition                                          |
| ------------------- | --------------------------------------------------- |
| `active_users`      | Total users in `profiles`                           |
| `total_jobs`        | Jobs with `active = true`                           |
| `total_searches`    | Rows in `searches` (all tracked searches)           |
| `total_saved_jobs`  | Rows in `saved_jobs`                                |
| `total_applications`| Rows in `applications`                              |
| `popular_companies` | Top 8 employers by active job count                 |
| `jobs_by_source`    | Active job count grouped by `source`                |

### GET `/admin/users`

`limit` query param (default 100), ordered by `created_at` descending. Returns an
array of `UserOut`.

```bash
curl "$API/admin/users?limit=50" -H "Authorization: Bearer $ADMIN_TOKEN"
```

### PATCH `/admin/users/{user_id}/role`

Change a user's role. See §1.

### POST `/admin/jobs`

Create a job from the admin console. Body is `JobCreate`:

```bash
curl -X POST "$API/admin/jobs" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "source": "manual",
    "title": "Staff Backend Engineer",
    "description": "Lead the platform team...",
    "company_name": "QuantumLabs",
    "location": "Pune, India",
    "remote": false,
    "salary_min": 3000000,
    "salary_max": 5000000,
    "salary_currency": "INR",
    "salary_text": "₹30L – ₹50L/yr",
    "job_type": "full_time",
    "level": "lead",
    "skills": ["Go", "Kubernetes"],
    "apply_url": "https://careers.example.com/staff-backend",
    "apply_on": "Company Website",
    "experience_min": 7,
    "experience_max": 12,
    "posted_at": "2026-08-15T00:00:00Z"
  }'
```

Returns **201** with the created `JobOut` (including generated `id`, `sponsored`,
`views`, `active: true`).

### PATCH `/admin/jobs/{job_id}/moderate`

Activate or deactivate a job. Inactive jobs are hidden from search, detail, and
suggestions.

```bash
# Hide a job
curl -X PATCH "$API/admin/jobs/e8b4f2a1-0000-0000-0000-000000000000/moderate?active=false" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Re-publish it
curl -X PATCH "$API/admin/jobs/e8b4f2a1-0000-0000-0000-000000000000/moderate?active=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Returns the updated `JobOut` with the new `active` value. A nonexistent job
returns **404**.

### POST `/admin/companies`

Create a company. Body is `CompanyCreate` (`name`, `slug`, optional `logo`,
`website`, `industry`, `description`, `location`, `size`, `rating`, `verified`).

```bash
curl -X POST "$API/admin/companies" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Nova Labs","slug":"nova-labs","industry":"SaaS","location":"Bengaluru, India"}'
```

Returns **201** with `{"created": true}`. (The full `CompanyOut` is returned by
the public `POST /api/v1/companies` admin route instead.)

### POST `/admin/broadcast`

Fan-out an in-app notification to **every** user. Query params: `title`
(required), `body` (optional). Each notification carries
`data: {"broadcast": true}`.

```bash
curl -X POST "$API/admin/broadcast?title=Maintenance+window&body=Scheduled+downtime+on+Sunday" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Returns **201**:

```json
{ "sent": 482 }
```

---

## 3. Moderation workflow

1. **Monitor** — watch `GET /admin/analytics` (`total_jobs`, `popular_companies`,
   `jobs_by_source`) and `GET /admin/jobs` search results for spam/duplicate/
   expired listings.
2. **Inspect** — fetch the job with `GET /api/v1/jobs/{job_id}` to review
   `description`, `apply_url`, and source.
3. **Hide** — `PATCH /admin/jobs/{id}/moderate?active=false` to take the listing
   down immediately without deleting it (preserves saved-job references, which use
   `ON DELETE SET NULL` / cascade rules).
4. **Fix or delete** — if a listing is salvageable, `POST /admin/jobs` a corrected
   version; otherwise deactivate. Adapters will not re-add a manually deactivated
   job with the same `external_id` + `source` only if the source feed stops
   emitting it — the ingestion upsert re-inserts anything the source still
   publishes, so pair moderation with an admin note in the job description or
   remove the source listing.

**Company moderation:** companies can be created or updated via the admin-required
routes `POST /companies`, `PATCH /companies/{slug}`, `DELETE /companies/{slug}`
(documentation in `docs/api.md` §5). Set `verified: true` to surface a company
higher in `GET /companies` ordering.

---

## 4. Broadcasting notifications

Two mechanisms:

1. **Manual broadcast** — `POST /admin/broadcast` (above) for announcements.
2. **Automated digests** — Celery beat runs `send_alert_digest` daily at 08:00 UTC,
   creating per-user notifications from their active `alerts`. Push to FCM happens
   through the `push_alert` task using registered `device_tokens`.

Both write rows to `notifications`, which users read via `GET /api/v1/notifications`
and mark read via `POST /notifications/{id}/read` or `POST /notifications/read-all`.

---

## 5. Analytics dashboard explanation

The dashboard is driven entirely by `GET /admin/analytics`:

- **Engagement line** — `active_users`, `total_searches`, `total_saved_jobs`,
  `total_applications` give the funnel: signups → search activity → save → apply.
  Compare `total_saved_jobs / active_users` and
  `total_applications / total_saved_jobs` to spot drop-off.
- **Supply chart** — `total_jobs` plus `jobs_by_source` shows catalog size and
  which adapters feed the most listings; a source at 0 suggests its adapter
  failed (check Celery ingestion logs for `Adapter <name> failed`).
- **Demand chart** — `popular_companies` (top 8 by active job count) shows where
  supply concentrates; useful for negotiating featured placements or surfacing
  company pages.

> Tip: there is no historical retention — counts are current snapshots. For
> trending charts, snapshot `GET /admin/analytics` into your own timeseries (e.g.
> a `daily_stats` table) on a schedule.