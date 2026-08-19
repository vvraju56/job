/* Shared TypeScript types mirroring the FastAPI backend schemas. */

export type JobSource = "linkedin" | "indeed" | "naukri" | "internshala" | "wellfound" | "company" | "manual" | "serpapi" | "usajobs" | "jsearch" | "greenhouse" | "ashby" | "remoteok";
export type JobType = "full_time" | "part_time" | "contract" | "internship" | "freelance";
export type Level = "entry" | "mid" | "senior" | "lead" | "executive";
export type AppStatus = "applied" | "interviewing" | "offered" | "rejected" | "withdrawn";
export type DatePosted = "today" | "3days" | "week" | "month";

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string | null;
  headline: string | null;
  bio: string | null;
  skills: string[];
  experience: number;
  location: string | null;
  resume_url: string | null;
  preferences: Record<string, unknown>;
  role: "user" | "admin";
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Job {
  id: string;
  source: JobSource;
  title: string;
  description: string | null;
  company_id: string | null;
  company_name: string;
  company_logo: string | null;
  location: string | null;
  remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_text: string | null;
  job_type: JobType;
  level: Level;
  skills: string[];
  apply_url: string;
  apply_on: string;
  experience_min: number;
  experience_max: number;
  posted_at: string | null;
  sponsored: boolean;
  views: number;
}

export interface JobList {
  total: number;
  page: number;
  page_size: number;
  items: Job[];
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  logo: string | null;
  website: string | null;
  industry: string | null;
  description: string | null;
  location: string | null;
  size: string | null;
  rating: number;
  review_count: number;
  verified: boolean;
  open_positions: number;
  created_at: string;
}

export interface Application {
  id: string;
  job_id: string | null;
  company_name: string | null;
  role: string | null;
  status: AppStatus;
  applied_url: string | null;
  notes: string | null;
  applied_at: string;
}

export interface SearchFilters {
  q?: string;
  location?: string;
  remote?: boolean;
  salary_min?: number;
  salary_max?: number;
  job_type?: JobType;
  level?: Level;
  experience_min?: number;
  experience_max?: number;
  source?: JobSource;
  company?: string;
  date_posted?: DatePosted;
  sort?: "recent" | "salary_desc" | "salary_asc" | "relevance";
  page?: number;
  page_size?: number;
}

export interface SearchSuggestion {
  title: string;
}

export interface Alert {
  id: string;
  query: string;
  filters: Record<string, unknown>;
  frequency: "instant" | "daily" | "weekly";
  active: boolean;
  created_at: string;
}

export interface AppNotification {
  id: string;
  title: string;
  body: string | null;
  data: Record<string, unknown>;
  read: boolean;
  created_at: string;
}

export interface ResumeAnalysis {
  ats_score: number;
  missing_keywords: string[];
  suggestions: string[];
  summary: string;
}

export interface SkillGap {
  current_skills: string[];
  missing_skills: string[];
  recommended_learning: string[];
}

export interface Analytics {
  active_users: number;
  total_jobs: number;
  total_searches: number;
  total_saved_jobs: number;
  total_applications: number;
  popular_companies: { name: string; count: number }[];
  jobs_by_source: { source: string; count: number }[];
}

export interface RecentSearch {
  endpoint: string;
  query: string | null;
  location: string | null;
  page: number;
  response_time_ms: number;
  cached: boolean;
  status_code: number;
  timestamp: string;
}

export interface CacheStats {
  backend: string;
  hits: number;
  misses: number;
  entries: number;
  hit_rate: number;
}

export interface ProviderHealth {
  name: string;
  configured: boolean;
}

export interface Usage {
  searches_used: number;
  monthly_limit: number;
  remaining: number;
  cache_hit_rate: number;
  total_requests: number;
  cache: CacheStats;
  provider: ProviderHealth;
  recent_searches: RecentSearch[];
}

export const JOB_TYPE_LABELS: Record<JobType, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  internship: "Internship",
  freelance: "Freelance",
};

export const LEVEL_LABELS: Record<Level, string> = {
  entry: "Entry Level",
  mid: "Mid Level",
  senior: "Senior",
  lead: "Lead",
  executive: "Executive",
};

export const SOURCE_LABELS: Record<JobSource, string> = {
  linkedin: "LinkedIn",
  indeed: "Indeed",
  naukri: "Naukri",
  internshala: "Internshala",
  wellfound: "Wellfound",
  company: "Company Website",
  manual: "Manual",
  serpapi: "Google Jobs",
  usajobs: "USAJobs",
  jsearch: "JSearch",
  greenhouse: "Greenhouse",
  ashby: "Ashby",
  remoteok: "Remote OK",
};

/** Tailwind badge classes per source (job source badges on cards). */
export const SOURCE_COLORS: Partial<Record<JobSource, string>> = {
  serpapi: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  usajobs: "border-blue-400/30 bg-blue-400/10 text-blue-300",
  jsearch: "border-purple-400/30 bg-purple-400/10 text-purple-300",
  greenhouse: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  ashby: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  remoteok: "border-zinc-400/30 bg-zinc-400/10 text-zinc-300",
};

export const APP_STATUS_LABELS: Record<AppStatus, string> = {
  applied: "Applied",
  interviewing: "Interviewing",
  offered: "Offered",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export const POPULAR_SEARCHES = [
  "Flutter Developer",
  "React Developer",
  "Backend Engineer",
  "Data Scientist",
  "UI/UX Designer",
  "DevOps Engineer",
];

export const CATEGORIES = [
  { label: "Frontend", icon: "code", query: "Frontend Developer" },
  { label: "Backend", icon: "server", query: "Backend Engineer" },
  { label: "Mobile", icon: "smartphone", query: "Flutter Developer" },
  { label: "Data & AI", icon: "brain", query: "Machine Learning" },
  { label: "Design", icon: "palette", query: "UI/UX Designer" },
  { label: "DevOps", icon: "cloud", query: "DevOps Engineer" },
  { label: "Product", icon: "layout", query: "Product Manager" },
  { label: "Marketing", icon: "megaphone", query: "Marketing" },
];