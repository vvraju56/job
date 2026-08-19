# Makeable Jobs

> **Tagline:** One Search. Every Opportunity.

Makeable Jobs is a production-ready **job aggregation platform**. It indexes job listings from multiple portals (LinkedIn, Indeed, Naukri, Internshala, Wellfound, company career pages) and redirects users to the **original application page**. It never owns or copies the jobs — every listing clearly shows *"Apply on Original Website"*.

## Monorepo Layout

```
.
├── web/        # Next.js 15 website (TypeScript, Tailwind, Framer Motion, shadcn-style UI)
├── mobile/     # Flutter app (Android & iOS) — Riverpod, GoRouter, Dio, FCM
├── backend/    # FastAPI REST API — SQLAlchemy, Redis, Celery, JWT, job adapters
├── supabase/   # PostgreSQL schema (users, jobs, companies, saved_jobs, ...)
└── docs/       # API reference + deployment guides
```

## Tech Stack

| Layer        | Technology                                             |
| ------------ | ------------------------------------------------------ |
| Website      | Next.js 15, React 19, TypeScript, Tailwind, Framer Motion |
| Mobile       | Flutter, Riverpod, GoRouter, Dio, Firebase Messaging   |
| Backend      | Python FastAPI, SQLAlchemy, Redis, Celery, JWT         |
| Database     | Supabase PostgreSQL                                    |
| Storage      | Supabase Storage                                       |
| Auth         | Email, Google, GitHub, LinkedIn OAuth                  |
| Notifications| Firebase Cloud Messaging + Email                       |
| AI           | OpenAI / Llama (resume, cover letter, skill gap, interview) |
| Deployment   | Vercel (web), Railway/Render (backend), Supabase (db)  |

## Brand

- **Colors:** Background `#050816`, Surface `#0F172A`, Primary `#3B82F6`, Secondary `#2563EB`, Accent `#60A5FA`, Success `#22C55E`, Warning `#F59E0B`, Text `#FFFFFF`, Muted `#94A3B8`
- **Style:** Dark gradient theme, glassmorphism cards, rounded corners, soft shadows, smooth animations, mobile-first responsive.

## Getting Started

```bash
# Website
cd web && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Supabase
# Run supabase/schema.sql in the Supabase SQL editor.

# Mobile
cd mobile && flutter pub get && flutter run
```

## Documentation

- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Architecture Notes](docs/architecture.md)

## Legal Note

Makeable Jobs is a **job aggregator**. All job content belongs to the original publisher. Users are redirected to the original portal (LinkedIn, Indeed, Naukri, Internshala, Wellfound, etc.) to apply. This project does not scrape copyrighted job descriptions into its own app; adapters only normalize publicly available listing metadata and point to the canonical URL.

© 2026 Makeable Jobs. All rights reserved. Made with ❤️ by **VV**.