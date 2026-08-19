import { api, API_URL } from "@/lib/api";
import type {
  Alert,
  Analytics,
  AppNotification,
  Application,
  AppStatus,
  CacheStats,
  Company,
  Job,
  JobList,
  ProviderHealth,
  ResumeAnalysis,
  SearchFilters,
  SkillGap,
  TokenPair,
  Usage,
  User,
} from "@/lib/types";

import type { AiProvider } from "@/components/tools/ai-key-input";

function jobPath(filters: SearchFilters = {}): string {
  const params = new URLSearchParams();
  const entries: [string, unknown][] = [
    ["query", filters.q],
    ["location", filters.location],
    ["remote", filters.remote],
    ["salary_min", filters.salary_min],
    ["salary_max", filters.salary_max],
    ["job_type", filters.job_type],
    ["level", filters.level],
    ["experience", filters.experience_min],
    ["date_posted", filters.date_posted],
    ["sort", filters.sort ?? "relevance"],
    ["page", filters.page ?? 1],
    ["page_size", filters.page_size ?? 20],
  ];
  for (const [key, value] of entries) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  return `/jobs/search?${params.toString()}`;
}

export const jobsService = {
  search: (filters: SearchFilters = {}) => api.get<JobList>(jobPath(filters)),
  trending: (limit = 6) => api.get<Job[]>(`/jobs/trending?limit=${limit}`),
  recommended: (limit = 8) => api.get<Job[]>(`/jobs/recommended?limit=${limit}`),
  detail: (id: string) => api.get<Job>(`/jobs/${id}`),
  similar: (id: string, limit = 5) => api.get<Job[]>(`/jobs/${id}/similar?limit=${limit}`),
  suggestions: (q: string, limit = 8) =>
    api.get<string[]>(`/jobs/search-suggestions?q=${encodeURIComponent(q)}&limit=${limit}`),
  save: (id: string) => api.post<{ saved: boolean }>(`/jobs/${id}/save`),
  unsave: (id: string) => api.delete(`/jobs/${id}/save`),
};

export const developerService = {
  usage: () => api.get<Usage>("/usage"),
  cacheStats: () => api.get<CacheStats>("/cache-stats"),
  health: () => api.get<ProviderHealth>("/health"),
};

export const companiesService = {
  list: (search?: string, limit = 24) =>
    api.get<Company[]>(
      `/companies${search ? `?search=${encodeURIComponent(search)}` : `?limit=${limit}`}`,
    ),
  featured: async (limit = 6) =>
    (await api.get<{ companies: Company[] }>(`/companies/featured?limit=${limit}`))
      .companies,
  detail: (slug: string) => api.get<Company>(`/companies/${slug}`),
};

export const authService = {
  register: (name: string, email: string, password: string) =>
    api.post<TokenPair>("/auth/register", { name, email, password }, { auth: false }),
  login: (email: string, password: string) =>
    api.post<TokenPair>("/auth/login", { email, password }, { auth: false }),
  googleLogin: (idToken: string) =>
    api.post<TokenPair>("/auth/google", { id_token: idToken }, { auth: false }),
  logout: () => api.post<null>("/auth/logout"),
  me: () => api.get<User>("/auth/me"),
};

export const usersService = {
  updateProfile: (patch: Partial<User>) => api.patch<User>("/users/me", patch),
  updatePreferences: (prefs: Record<string, unknown>) =>
    api.patch<User>("/users/me/preferences", prefs),
  savedJobs: async () => (await api.get<{ jobs: Job[] }>("/users/me/saved-jobs")).jobs,
  applications: async (status?: AppStatus) =>
    (
      await api.get<{ applications: Application[] }>(
        `/users/me/applications${status ? `?status_filter=${status}` : ""}`,
      )
    ).applications,
  createApplication: (payload: {
    job_id?: string;
    company_name?: string;
    role?: string;
    applied_url?: string;
    status?: AppStatus;
  }) => api.post<Application>("/users/me/applications", payload),
  updateApplication: (id: string, status: AppStatus, notes?: string) =>
    api.patch<Application>(`/users/me/applications/${id}`, { status, notes }),
  deleteApplication: (id: string) => api.delete(`/users/me/applications/${id}`),
  recentSearches: (limit = 10) =>
    api.get<unknown[]>(`/users/me/searches?limit=${limit}`),
};

export const resumeService = {
  analyze: (payload: {
    resume_text: string;
    target_role?: string;
    job_description?: string;
    api_key?: string;
    provider?: AiProvider;
  }) => api.post<ResumeAnalysis>("/resume/analyze", payload),
  coverLetter: (payload: {
    resume_text: string;
    job_title: string;
    company_name: string;
    job_description?: string;
    api_key?: string;
    provider?: AiProvider;
  }) => api.post<{ cover_letter: string }>("/resume/cover-letter", payload),
  skillGap: (payload: {
    resume_text: string;
    target_role: string;
    api_key?: string;
    provider?: AiProvider;
  }) => api.post<SkillGap>("/resume/skill-gap", payload),
  interviewPrep: (payload: {
    job_title: string;
    job_description?: string;
    resume_text?: string;
    api_key?: string;
    provider?: AiProvider;
  }) => api.post<{ questions: string[] }>("/resume/interview-prep", payload),
};

export const notificationsService = {
  list: async (unreadOnly = false, limit = 50) =>
    (
      await api.get<{ notifications: AppNotification[] }>(
        `/notifications/?unread_only=${unreadOnly}&limit=${limit}`,
      )
    ).notifications,
  markRead: (id: string) => api.post<AppNotification>(`/notifications/${id}/read`),
  markAllRead: () => api.post<null>("/notifications/read-all"),
  alerts: async () => (await api.get<{ alerts: Alert[] }>("/notifications/alerts")).alerts,
  createAlert: (payload: {
    query: string;
    filters?: Record<string, unknown>;
    frequency?: string;
  }) => api.post<Alert>("/notifications/alerts", payload),
  deleteAlert: (id: string) => api.delete(`/notifications/alerts/${id}`),
  registerDevice: (token: string, platform: string) =>
    api.post("/notifications/device-token", { token, platform }),
};

export const adminService = {
  analytics: () => api.get<Analytics>("/admin/analytics"),
  users: (limit = 100) => api.get<User[]>(`/admin/users?limit=${limit}`),
  setRole: (userId: string, role: "user" | "admin") =>
    api.patch<User>(`/admin/users/${userId}/role?role=${role}`),
  moderateJob: (jobId: string, active: boolean) =>
    api.patch<Job>(`/admin/jobs/${jobId}/moderate?active=${active}`),
  broadcast: (title: string, body?: string) =>
    api.post<{ sent: number }>(`/admin/broadcast?title=${encodeURIComponent(title)}${body ? `&body=${encodeURIComponent(body)}` : ""}`),
};

export { API_URL };