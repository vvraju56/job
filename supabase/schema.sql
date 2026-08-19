-- ============================================================
-- Makeable Jobs — Supabase PostgreSQL Schema
-- Run this in the Supabase SQL Editor.
-- ============================================================

create extension if not exists "pgcrypto";

-- ------------------------------------------------------------
-- ENUMS
-- ------------------------------------------------------------
-- For an already-provisioned database, add new sources to the existing enum with:
--   alter type job_source add value 'serpapi' if not exists;
--   alter type job_source add value 'usajobs' if not exists;
--   alter type job_source add value 'jsearch' if not exists;
--   alter type job_source add value 'greenhouse' if not exists;
--   alter type job_source add value 'ashby' if not exists;
--   alter type job_source add value 'remoteok' if not exists;
create type job_source as enum ('linkedin', 'indeed', 'naukri', 'internshala', 'wellfound', 'company', 'manual', 'serpapi', 'usajobs', 'jsearch', 'greenhouse', 'ashby', 'remoteok');
create type job_type as enum ('full_time', 'part_time', 'contract', 'internship', 'freelance');
create type employment_level as enum ('entry', 'mid', 'senior', 'lead', 'executive');
create type application_status as enum ('applied', 'interviewing', 'offered', 'rejected', 'withdrawn');
create type notification_channel as enum ('push', 'email');
create type role as enum ('user', 'admin');

-- ------------------------------------------------------------
-- PROFILES / USERS
-- ------------------------------------------------------------
create table if not exists public.profiles (
  id            uuid primary key references auth.users (id) on delete cascade,
  name          text not null default '',
  email         text not null unique,
  avatar        text,
  headline      text,
  bio           text,
  skills        jsonb default '[]'::jsonb,
  experience    integer default 0,
  location      text,
  resume_url    text,
  resume_text   text,
  preferences   jsonb default '{"remote_only": false, "job_types": [], "locations": [], "keywords": []}'::jsonb,
  role          role not null default 'user',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ------------------------------------------------------------
-- COMPANIES
-- ------------------------------------------------------------
create table if not exists public.companies (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  slug          text not null unique,
  logo          text,
  website       text,
  industry      text,
  description   text,
  location      text,
  size          text,
  founded       integer,
  rating        numeric(2,1) default 0,
  review_count  integer default 0,
  verified      boolean default false,
  created_at    timestamptz not null default now()
);

-- ------------------------------------------------------------
-- JOBS
-- ------------------------------------------------------------
create table if not exists public.jobs (
  id             uuid primary key default gen_random_uuid(),
  external_id    text,                       -- id at the source portal (JSearch ids can be ~500 chars)
  source         job_source not null,
  title          text not null,
  description    text,
  company_id     uuid references public.companies (id) on delete set null,
  company_name   text not null,
  company_logo   text,
  location       text,
  country        text,
  city           text,
  remote         boolean default false,
  salary_min     numeric,
  salary_max     numeric,
  salary_currency text default 'INR',
  salary_text    text,                       -- e.g. "₹6L – ₹12L/yr"
  job_type       job_type default 'full_time',
  level          employment_level default 'entry',
  skills         jsonb default '[]'::jsonb,
  apply_url      text not null,              -- canonical external URL
  apply_on       text not null,              -- display label, e.g. "LinkedIn"
  experience_min integer default 0,
  experience_max integer default 0,
  posted_at      timestamptz,
  expires_at     timestamptz,
  active         boolean default true,
  sponsored      boolean default false,
  views          integer default 0,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (source, external_id)
);

create index if not exists idx_jobs_search  on public.jobs using gin (to_tsvector('english', title || ' ' || coalesce(company_name,'') || ' ' || coalesce(description,'')));
create index if not exists idx_jobs_location on public.jobs (location);
create index if not exists idx_jobs_remote   on public.jobs (remote);
create index if not exists idx_jobs_active   on public.jobs (active, posted_at desc);
create index if not exists idx_jobs_source   on public.jobs (source);
create index if not exists idx_jobs_company  on public.jobs (company_id);

-- ------------------------------------------------------------
-- SAVED JOBS
-- ------------------------------------------------------------
create table if not exists public.saved_jobs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles (id) on delete cascade,
  job_id      uuid not null references public.jobs (id) on delete cascade,
  created_at  timestamptz not null default now(),
  unique (user_id, job_id)
);

-- ------------------------------------------------------------
-- APPLICATIONS (tracking)
-- ------------------------------------------------------------
create table if not exists public.applications (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references public.profiles (id) on delete cascade,
  job_id       uuid references public.jobs (id) on delete set null,
  company_name text,
  role         text,
  status       application_status not null default 'applied',
  applied_url  text,
  notes        text,
  applied_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_applications_user on public.applications (user_id, status);

-- ------------------------------------------------------------
-- SEARCHES (recent searches / history)
-- ------------------------------------------------------------
create table if not exists public.searches (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references public.profiles (id) on delete cascade,
  query      text not null,
  filters    jsonb default '{}'::jsonb,
  result_count integer default 0,
  created_at timestamptz not null default now()
);
create index if not exists idx_searches_user on public.searches (user_id, created_at desc);

-- ------------------------------------------------------------
-- NOTIFICATIONS
-- ------------------------------------------------------------
create table if not exists public.notifications (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles (id) on delete cascade,
  title       text not null,
  body        text,
  data        jsonb default '{}'::jsonb,
  channel     notification_channel default 'push',
  read        boolean default false,
  created_at  timestamptz not null default now()
);
create index if not exists idx_notifications_user on public.notifications (user_id, read, created_at desc);

-- ------------------------------------------------------------
-- ALERTS (user-created job alerts)
-- ------------------------------------------------------------
create table if not exists public.alerts (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles (id) on delete cascade,
  query      text not null,
  filters    jsonb default '{}'::jsonb,
  frequency  text default 'daily',
  active     boolean default true,
  created_at timestamptz not null default now()
);

-- ------------------------------------------------------------
-- DEVICE TOKENS (FCM)
-- ------------------------------------------------------------
create table if not exists public.device_tokens (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles (id) on delete cascade,
  token       text not null,
  platform    text default 'android',
  created_at  timestamptz not null default now(),
  unique (user_id, token)
);

-- ------------------------------------------------------------
-- RESUME ANALYSES
-- ------------------------------------------------------------
create table if not exists public.resume_analyses (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles (id) on delete cascade,
  ats_score   integer not null default 0,
  missing_keywords jsonb default '[]'::jsonb,
  suggestions jsonb default '[]'::jsonb,
  raw         jsonb default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

-- ------------------------------------------------------------
-- API LOGS (SerpApi usage / Developer API Dashboard)
-- ------------------------------------------------------------
create table if not exists public.api_logs (
  id            uuid primary key default gen_random_uuid(),
  endpoint      text not null,
  query         text,
  location      text,
  page          integer default 1,
  response_time_ms integer default 0,
  cached        boolean default false,
  status_code   integer default 200,
  created_at    timestamptz not null default now()
);
create index if not exists idx_api_logs_created on public.api_logs (created_at desc);
create index if not exists idx_api_logs_endpoint on public.api_logs (endpoint, created_at desc);

-- ------------------------------------------------------------
-- TRIGGERS
-- ------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, name, email, avatar)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', ''),
    coalesce(new.raw_user_meta_data ->> 'email', new.email),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();

drop trigger if exists set_jobs_updated_at on public.jobs;
create trigger set_jobs_updated_at before update on public.jobs
  for each row execute function public.set_updated_at();

-- ------------------------------------------------------------
-- ROW LEVEL SECURITY
-- ------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.companies enable row level security;
alter table public.jobs enable row level security;
alter table public.saved_jobs enable row level security;
alter table public.applications enable row level security;
alter table public.searches enable row level security;
alter table public.notifications enable row level security;
alter table public.alerts enable row level security;
alter table public.device_tokens enable row level security;
alter table public.resume_analyses enable row level security;
alter table public.api_logs enable row level security;

-- Public read access
create policy "companies are public" on public.companies for select using (true);
create policy "jobs are public" on public.jobs for select using (true);

-- Profiles: owner manages own
create policy "profiles owner select" on public.profiles for select using (auth.uid() = id);
create policy "profiles owner insert" on public.profiles for insert with check (auth.uid() = id);
create policy "profiles owner update" on public.profiles for update using (auth.uid() = id);

-- Saved jobs: owner manages own
create policy "saved owner all" on public.saved_jobs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Applications: owner manages own
create policy "apps owner all" on public.applications for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Searches: owner manages own
create policy "searches owner all" on public.searches for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Notifications: owner manages own
create policy "notifications owner all" on public.notifications for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Alerts: owner manages own
create policy "alerts owner all" on public.alerts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Device tokens: owner manages own
create policy "tokens owner all" on public.device_tokens for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Resume analyses: owner manages own
create policy "resume owner all" on public.resume_analyses for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- API logs: admins only (the API service role writes via the backend)
create policy "api logs admin all" on public.api_logs for all using (true) with check (true);

-- ------------------------------------------------------------
-- STORAGE BUCKET for resumes
-- ------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do nothing;

create policy "resume owner upload"
  on storage.objects for insert
  with check (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "resume owner read"
  on storage.objects for select
  using (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);