import type { MetadataRoute } from "next";

import { serverApi } from "@/lib/server-api";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, changeFrequency: "daily", priority: 1 },
    { url: `${BASE_URL}/jobs`, changeFrequency: "hourly", priority: 0.9 },
    { url: `${BASE_URL}/companies`, changeFrequency: "daily", priority: 0.7 },
    { url: `${BASE_URL}/tools`, changeFrequency: "weekly", priority: 0.6 },
    { url: `${BASE_URL}/tools/resume-score`, changeFrequency: "weekly", priority: 0.5 },
    { url: `${BASE_URL}/tools/cover-letter`, changeFrequency: "weekly", priority: 0.5 },
    { url: `${BASE_URL}/tools/skill-gap`, changeFrequency: "weekly", priority: 0.5 },
    { url: `${BASE_URL}/tools/interview`, changeFrequency: "weekly", priority: 0.5 },
  ];

  let jobRoutes: MetadataRoute.Sitemap = [];
  let companyRoutes: MetadataRoute.Sitemap = [];
  try {
    const [jobs, companies] = await Promise.all([
      serverApi.jobs({ page_size: 100 }),
      serverApi.companies(100),
    ]);
    jobRoutes = jobs.items.map((job) => ({
      url: `${BASE_URL}/jobs/${job.id}`,
      lastModified: job.posted_at ?? undefined,
      changeFrequency: "daily" as const,
      priority: 0.8,
    }));
    companyRoutes = companies.map((c) => ({
      url: `${BASE_URL}/companies/${c.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.6,
    }));
  } catch {
    /* sitemap degrades gracefully if API is down */
  }

  return [...staticRoutes, ...jobRoutes, ...companyRoutes];
}