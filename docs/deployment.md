# Makeable Jobs — Deployment Guide

This guide covers deploying every part of the Makeable Jobs platform:

| Component | Where                                          |
| --------- | ---------------------------------------------- |
| Website   | Next.js 15 → **Vercel**                        |
| Backend   | FastAPI → **Railway** or **Render**            |
| Workers   | Celery + Redis → same platform as backend      |
| Database  | Supabase PostgreSQL + Storage                  |
| Mobile    | Flutter → Play Store / App Store               |
| Static    | Optional `public/` site → Cloudflare Workers   |

Monorepo layout recap:

```
.
├── web/        # Next.js 15 website
├── mobile/     # Flutter app (Android & iOS)
├── backend/    # FastAPI REST API
├── supabase/   # schema.sql
├── public/     # optional static marketing site
└── docs/
```

---

## 1. Supabase (database + storage) — do this first

The backend and every other component depend on the database.

### 1.1 Create the project

1. Create a project at <https://supabase.com/dashboard>.
2. Note the **Project URL** (e.g. `https://xyzcompany.supabase.co`) and the
   **Database password**.
3. Copy the connection string from **Settings → Database → Connection string →
   URI**. It looks like:
   ```
   postgresql://postgres.xxxx:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
   ```

### 1.2 Apply the schema

1. Open the **SQL Editor** in the Supabase dashboard.
2. Paste the full contents of `supabase/schema.sql` and click **Run**.

This creates all 10 tables (`profiles`, `companies`, `jobs`, `saved_jobs`,
`applications`, `searches`, `notifications`, `alerts`, `device_tokens`,
`resume_analyses`), the enums, indexes (including the full-text GIN index for job
search), triggers, RLS policies, and the `resumes` storage bucket.

### 1.3 Verify the storage bucket

`schema.sql` inserts a private bucket named `resumes`. Confirm under
**Storage → Buckets** that it exists and is private. The RLS policies only allow
users to upload/list objects under `resumes/<auth-uid>/...`.

### 1.4 Auth providers

In **Authentication → Providers**:

- **Email** — enable; optionally turn on "Confirm email".
- **Google** — enable and provide the OAuth Client ID/Secret from Google Cloud
  Console.
- **GitHub** — enable with Client ID/Secret from GitHub OAuth apps.
- **LinkedIn** — enable with Client ID/Secret from LinkedIn developer apps.

Each provider's callback URL is shown in the Supabase UI and must be added to the
provider's console (e.g. `https://xyzcompany.supabase.co/auth/v1/callback`).

The trigger `on_auth_user_created` automatically creates a `profiles` row when a
new `auth.users` row appears, so social logins work without extra code.

### 1.5 RLS notes

- `companies` and `jobs` are **publicly readable** (`using (true)`) — fine because
  the API service role bypasses RLS anyway; these policies support direct Supabase
  clients if you ever use them.
- All user-owned tables (`profiles`, `saved_jobs`, `applications`, `searches`,
  `notifications`, `alerts`, `device_tokens`, `resume_analyses`) only allow the
  owning `auth.uid()` to read/write their own rows.
- Writes from the FastAPI backend use the **service role key**, which bypasses RLS.
  The policies are defense-in-depth for direct client access.

### 1.6 Service role key

Generate the anon + **service_role** keys under **Settings → API**.
`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the backend `.env` use the
service role key. **Never** expose the service role key to the browser or app.

---

## 2. Backend — FastAPI (Railway or Render)

### 2.1 Environment variables

Copy `backend/.env.example` to `.env` and fill in:

| Variable                  | Example                                                       | Notes                                             |
| ------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| `APP_NAME`                | `Makeable Jobs API`                                           |                                                   |
| `APP_ENV`                 | `production`                                                  |                                                   |
| `DEBUG`                   | `false`                                                       |                                                   |
| `SECRET_KEY`              | long random string                                            | **must** be unique per environment                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                                      |                                                   |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14`                                                        |                                                   |
| `ALGORITHM`               | `HS256`                                                       |                                                   |
| `DATABASE_URL`            | `postgresql+asyncpg://postgres.xxx:pass@host:5432/postgres`   | Supabase URI with `+asyncpg` driver               |
| `REDIS_URL`               | `rediss://default:pass@...`                                   | For Celery **and** the job-search cache (Upstash/Railway Redis) |
| `CELERY_BROKER_URL`       | same as `REDIS_URL`                                           |                                                   |
| `CELERY_RESULT_BACKEND`   | same as `REDIS_URL` (DB 1)                                    |                                                   |
| `CORS_ORIGINS`            | `https://makeable-jobs.vercel.app,https://your-app.com`       | comma-separated                                   |
| `FIREBASE_CREDENTIALS`    | path to service-account JSON                                  | for FCM push                                      |
| `FIREBASE_CREDENTIALS_JSON` | raw service-account JSON (single line)                     | **preferred on Render/Vercel** — no file upload needed |
| `OPENAI_API_KEY`          | optional                                                      | empty → heuristic fallback                        |
| `OPENAI_BASE_URL`         | `https://api.openai.com/v1`                                   |                                                   |
| `AI_MODEL`                | `gpt-4o-mini`                                                 |                                                   |
| `LLAMA_BASE_URL`          | optional                                                      | if using a self-hosted Llama endpoint             |
| `LLAMA_MODEL`             | `llama3.1`                                                    |                                                   |
| `SUPABASE_URL`            | `https://xyzcompany.supabase.co`                              | optional direct client                            |
| `SUPABASE_SERVICE_ROLE_KEY` | service-role JWT                                           | keep secret                                       |
| `JOB_PROVIDER`            | `serpapi`                                                     | default provider                                  |
| `ENABLED_PROVIDERS`       | `serpapi,jsearch,usajobs,remoteok`                            | providers queried by `/jobs/search`              |
| `SERPAPI_API_KEY`         | from https://serpapi.com (free plan ~250 searches/month)      | **required for live search**; empty → DB fallback |
| `SERPAPI_GL`              | `IN`                                                          | Google geo; set to your target country            |
| `SERPAPI_MONTHLY_LIMIT`   | `250`                                                         | matches your SerpApi plan                         |
| `SERPAPI_CACHE_TTL_HOURS` | `6`                                                           | job-search cache TTL                              |
| `USAJOBS_API_KEY`         | from https://developer.usajobs.gov                           | optional; enables federal jobs                    |
| `USAJOBS_EMAIL`           | your email (must be in the User-Agent)                       | required together with the USAJobs key            |
| `JSEARCH_API_KEY`         | from your JSearch/openwebninja provider                      | optional; enables multi-source JSearch            |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | bootstrap admin creds                                   | used by seed scripts                              |

### 2.2 Run the API

The FastAPI app object is `app.main:app`.

**Development:**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Production (gunicorn + uvicorn workers):**

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### 2.3 Run the Celery worker + beat

The backend ships with a Celery app in `app/workers/celery_app.py` with two
scheduled jobs:

| Task                          | Schedule          | Purpose                              |
| ----------------------------- | ----------------- | ------------------------------------ |
| `app.workers.tasks.ingest_jobs`  | hourly at `:15` | Run job adapters and upsert listings |
| `app.workers.tasks.send_alert_digest` | daily 08:00 UTC | Create notifications from user alerts |

**Worker:**

```bash
celery -A app.workers.celery_app:celery_app worker --loglevel=info --concurrency=4
```

**Beat scheduler:**

```bash
celery -A app.workers.celery_app:celery_app beat --loglevel=info
```

> On **Railway** and **Render** run these as *separate services* (or a second
> process), not in the same dyno as the web server.

### 2.4 Railway

1. New Project → Deploy from the `backend/` directory (or a monorepo subpath).
2. **Settings → Start Command**:
   ```
   gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4
   ```
3. Add a **Redis** plugin from the Railway marketplace → copy its `REDIS_URL`
   (make sure TLS URLs use `rediss://` for asyncpg/celery).
4. Add a second service with start command:
   ```
   celery -A app.workers.celery_app:celery_app worker --loglevel=info
   ```
   and a third:
   ```
   celery -A app.workers.celery_app:celery_app beat --loglevel=info
   ```
5. Set all env vars from §2.1 in each service (Railway lets you reference a shared
   variable group).
6. Point `DATABASE_URL` at Supabase using the **Pooler** connection string. If you
   use the transaction pooler, set `sslmode=require` — Railway/backend connections
   are outbound so pooled connections are fine.

### 2.5 Render

1. Create a **Web Service** from the `backend/` repo/directory.
2. **Build Command**:
   ```
   pip install -r requirements.txt
   ```
3. **Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Blueprint (recommended):** a `render.yaml` is included at the repo root and
   references `rootDir: backend`, the health check on `/health`, and every
   environment variable marked `sync: false` (set them in the dashboard). Import
   it via **New → Blueprint** instead of creating the service manually.
5. **Database schema:** on startup (outside local dev) the app runs
   `alembic upgrade head` against `DATABASE_URL`, creating all tables if the
   Supabase schema was not applied manually. Either run `supabase/schema.sql`
   first or let the automatic migration create it.
6. Add a **Redis** instance from the Render dashboard and set
   `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` to `rediss://...`
   (optional — without Redis the search cache and Celery are disabled).
7. Set Firebase via **`FIREBASE_CREDENTIALS_JSON`** (paste the raw service-account
   JSON) instead of uploading a file.
8. Create **Background Workers** (Worker type) for Celery:
   ```
   celery -A app.workers.celery_app:celery_app worker --loglevel=info
   ```
   and a separate one for beat:
   ```
   celery -A app.workers.celery_app:celery_app beat --loglevel=info
   ```
9. Enable a **Health Check** on `/health` (returns 200 JSON `{"status":"ok",...}`).

### 2.6 Verifying the deployment

```bash
curl https://<api-host>/health
# → {"status":"ok","app":"Makeable Jobs API","env":"production"}

curl https://<api-host>/api/v1/openapi.json | head -c 200
curl https://<api-host>/docs
```

---

## 3. Website — Next.js 15 (Vercel)

### 3.1 Prerequisites

The website lives in `web/`. It uses **Next.js 15**, React 19, TypeScript,
Tailwind CSS, Framer Motion, and a shadcn-style UI.

### 3.2 Deploy

1. Push the repo to GitHub/GitLab.
2. In Vercel: **Add New → Project** and import the repo.
3. Set **Root Directory** to `web`.
4. **Framework Preset** will auto-detect `Next.js` (build command
   `next build`, output directory `.next`).

### 3.3 Environment variables

| Variable                  | Example                             | Notes                        |
| ------------------------- | ----------------------------------- | ---------------------------- |
| `NEXT_PUBLIC_API_URL`     | `https://makeable-jobs-api.onrender.com/api/v1` | full API base incl. `/api/v1` (client appends paths like `/jobs/search`) |
| `NEXT_PUBLIC_SITE_URL`    | `https://makeable-jobs.vercel.app`  | canonical/sitemap URL        |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | `AIza...`                     | Google sign-in (matches `web/lib/firebase.ts`) |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | `makeable-jobs.firebaseapp.com` | |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | `makeable-jobs`            | |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | `makeable-jobs.firebasestorage.app` | |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | `137341150950` | |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | `1:137341150950:web:a516b481df4f5c5ec5fd27` | |

> Set `NEXT_PUBLIC_*` variables — Next.js inlines them at build time and they are
> safe to expose in the browser. Server-side secrets (backend credentials) never
> belong in the web app.

### 3.4 Build settings

- **Build Command:** `npm run build`
- **Install Command:** `npm install`
- **Output:** `.next` (auto)
- Node.js version: **20.x or 22.x** (Next.js 15 requirement).

### 3.5 Post-deploy checks

- The `CORS_ORIGINS` value on the backend must include the Vercel domain
  (`https://makeable-jobs.vercel.app` or your custom domain).
- Enable **Production + Preview** deployment branches if you want preview URLs.
- Custom domain: **Domains** tab in Vercel, then add it to backend CORS.

---

## 4. Mobile — Flutter

### 4.1 Configuration for the environment

The Flutter app reads the API base URL from a build-time define:

```bash
flutter run --dart-define=API_BASE_URL=https://makeable-api.up.railway.app/api/v1
flutter build apk --dart-define=API_BASE_URL=https://makeable-api.up.railway.app/api/v1
```

> Android emulator reaching your local machine: use
> `--dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1`. iOS simulator can use
> `localhost`.

### 4.2 Android — release APK / AAB

Requirements: minSdk **23**, applicationId `com.makeable.jobs`.

```bash
cd mobile
flutter pub get
flutter build apk --release
```

For the Play Store you must build an **AAB** and sign it with your release key:

```bash
flutter build appbundle --release
```

**Signing:** the checked-in Gradle config uses the debug signing key so
`flutter run` works out of the box. Before release:

1. Generate a keystore: `keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload`
2. Create `android/key.properties`:
   ```properties
   storePassword=...
   keyPassword=...
   keyAlias=upload
   storeFile=release.jks
   ```
3. Wire `signingConfig signingConfigs.release` into `android/app/build.gradle`
   (see the commented block) so `flutter build appbundle --release` signs the AAB.

### 4.3 Play Store checklist

- [ ] AAB built and signed with a dedicated upload key
- [ ] Screenshots (phone + tablet), feature graphic, icon (512×512)
- [ ] App description + content rating questionnaire
- [ ] Data safety form (no personal data sold; auth + notifications declared)
- [ ] Privacy policy URL (public)
- [ ] App categories: **Jobs** / **Business**
- [ ] FCM configured (see §4.5) so push notifications work in review builds
- [ ] Test on Android 10–14 before rollout

### 4.4 App Store (iOS) checklist

Requirements: iOS 12.0+, CocoaPods installed, Xcode with a valid team.

```bash
cd mobile
flutter build ios --release
open ios/Runner.xcworkspace
```

In Xcode:
- Set **Signing & Capabilities → Team**, bundle id `com.makeable.jobs`.
- Enable **Push Notifications** capability.
- Enable **Background Modes → Remote notifications**.

Then **Product → Archive → Distribute → App Store Connect**.

Checklist:
- [ ] Privacy manifest entries for push tokens / usage strings
- [ ] `App Store` privacy labels (cookies, contact info) in App Store Connect
- [ ] Test notifications with a real device (APNs sandbox → production)
- [ ] Screenshots for required device sizes (6.9", 6.5", 5.5")
- [ ] Export compliance answered in App Store Connect

### 4.5 Firebase setup for FCM (push notifications)

The app uses `firebase_core` + `firebase_messaging`. Because
`lib/firebase_options.dart` is machine-specific it is **not committed** — you must
generate it once:

1. Create a project at <https://console.firebase.google.com>.
2. Add an **Android app** (package `com.makeable.jobs`) and an **iOS app**
   (bundle id `com.makeable.jobs`).
3. Install the FlutterFire CLI:
   ```bash
   dart pub global activate flutterfire_cli
   ```
4. From `mobile/`, generate the config:
   ```bash
   flutterfire configure --project=<your-project-id>
   ```
   This writes:
   - `mobile/lib/firebase_options.dart`
   - `mobile/android/app/google-services.json`
   - `mobile/ios/Runner/GoogleService-Info.plist`
5. **(Android only)** ensure the Google Services Gradle plugin is enabled in
   `android/settings.gradle` and `android/app/build.gradle`.

Until step 4 is done, notifications are disabled but the rest of the app works —
`FcmService` fails gracefully.

6. On the backend, point `FIREBASE_CREDENTIALS` at the service-account JSON
   (Project Settings → Service accounts → Generate new private key) so the server
   can send pushes (`firebase-admin`).

**Push pipeline:** the mobile app registers its token via
`POST /api/v1/notifications/device-token` (see `docs/api.md`). Celery's
`push_alert` task fans out to all of a user's device tokens.

---

## 5. Optional — Cloudflare Workers static hosting

The repo includes `wrangler.jsonc` for serving the `public/` directory as a static
site on Cloudflare Workers:

```jsonc
{
  "name": "job",
  "compatibility_date": "2025-08-10",
  "assets": {
    "directory": "./public",
    "not_found_handling": "404-page"
  }
}
```

```bash
npm i -g wrangler
wrangler login
wrangler deploy            # upload assets + worker
wrangler publish --dry-run # preview
```

`not_found_handling: "404-page"` returns the static 404 page for unknown routes.
Point your domain at the Workers project in the Cloudflare dashboard. Use this for
a lightweight marketing/landing page that doesn't need server rendering.

---

## 6. Production checklist (all components)

- [ ] `SECRET_KEY` replaced with a long random value, rotated before launch
- [ ] `DEBUG=false`, `APP_ENV=production`
- [ ] CORS restricted to real origins
- [ ] Supabase service role key only in backend env, never in client code
- [ ] Rate limiting active (slowapi, 200/min default)
- [ ] Celery beat running (hourly ingestion + daily alert digest)
- [ ] `/health` health-check hooked up on the hosting platform
- [ ] Custom domain on Vercel added to backend `CORS_ORIGINS`
- [ ] Play/App Store store listings + privacy policy published
- [ ] FCM service account present on the backend for push notifications