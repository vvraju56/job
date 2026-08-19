import { API_URL } from "@/lib/api";
import type { Company, Job, JobList, SearchFilters } from "@/lib/types";
import { buildQueryString } from "@/lib/utils";

export const SERVER_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Server-side data helpers. Run inside Server Components / Route Handlers.
 * These endpoints are public and need no auth token.
 */

async function serverFetch<T>(path: string, revalidate = 60): Promise<T> {
  const res = await fetch(`${SERVER_API_URL}${path}`, {
    next: { revalidate },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} for ${path}`);
  }
  return (await res.json()) as T;
}

function jobPath(filters: SearchFilters = {}): string {
  const entries: [string, unknown][] = [
    ["q", filters.q],
    ["location", filters.location],
    ["remote", filters.remote],
    ["salary_min", filters.salary_min],
    ["salary_max", filters.salary_max],
    ["job_type", filters.job_type],
    ["level", filters.level],
    ["experience_min", filters.experience_min],
    ["experience_max", filters.experience_max],
    ["source", filters.source],
    ["company", filters.company],
    ["sort", filters.sort ?? "recent"],
    ["page", filters.page ?? 1],
    ["page_size", filters.page_size ?? 20],
  ];
  return `/jobs${buildQueryString(Object.fromEntries(entries))}`;
}

export const serverApi = {
  jobs: (filters: SearchFilters = {}) => serverFetch<JobList>(jobPath(filters)),
  job: (id: string) => serverFetch<Job>(`/jobs/${id}`, 30),
  trendingJobs: (limit = 6) => serverFetch<Job[]>(`/jobs/trending?limit=${limit}`),
  similarJobs: (id: string, limit = 5) =>
    serverFetch<Job[]>(`/jobs/${id}/similar?limit=${limit}`),
  companies: (limit = 24) => serverFetch<Company[]>(`/companies?limit=${limit}`),
  featuredCompanies: (limit = 6) =>
    serverFetch<Company[]>(`/companies/featured?limit=${limit}`),
  company: (slug: string) => serverFetch<Company>(`/companies/${slug}`),
  companyJobs: (companyName: string, limit = 20) =>
    serverFetch<JobList>(
      `/jobs?company=${encodeURIComponent(companyName)}&page_size=${limit}`,
      30,
    ),
};

export function resolveJobUrl(id: string) {
  return `${SERVER_API_URL}/jobs/${id}`;
}