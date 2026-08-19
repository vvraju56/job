import type { Metadata } from "next";

import { CategoriesSection } from "@/components/home/categories-section";
import { HeroSection } from "@/components/home/hero-section";
import { StatsSection } from "@/components/home/stats-section";
import { ToolsSection } from "@/components/home/tools-section";
import { CompaniesGrid } from "@/components/companies/companies-grid";
import { JobsGrid } from "@/components/jobs/jobs-grid";
import { SectionHeading } from "@/components/ui/section-heading";
import { serverApi } from "@/lib/server-api";

export const metadata: Metadata = {
  title: "Makeable Jobs — One Search. Every Opportunity.",
  description:
    "Search and discover jobs from LinkedIn, Indeed, Naukri, Internshala, Wellfound and company career pages. Apply on the original website.",
};

export default async function HomePage() {
  const [latestJobs, remoteJobs, featuredCompanies] = await Promise.all([
    serverApi.jobs({ sort: "recent", page_size: 6 }).catch(() => null),
    serverApi.jobs({ remote: true, sort: "recent", page_size: 6 }).catch(() => null),
    serverApi.featuredCompanies(6).catch(() => []),
  ]);

  return (
    <>
      <HeroSection />
      <StatsSection />
      <CategoriesSection />

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <SectionHeading
          eyebrow="Fresh Listings"
          title="Latest Jobs"
          subtitle="The most recent opportunities aggregated from across the web."
          actionHref="/jobs"
          actionLabel="View all jobs"
        />
        <JobsGrid jobs={latestJobs?.items ?? []} loading={!latestJobs} />
      </section>

      <section className="bg-surface/40 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeading
            eyebrow="Work From Anywhere"
            title="Remote Jobs"
            subtitle="Fully remote roles from companies hiring across the globe."
            actionHref="/jobs?remote=true"
            actionLabel="Browse remote jobs"
          />
          <JobsGrid jobs={remoteJobs?.items ?? []} loading={!remoteJobs} />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <SectionHeading
          eyebrow="Top Employers"
          title="Featured Companies"
          subtitle="Companies with the most open positions on Makeable Jobs."
          actionHref="/companies"
          actionLabel="View all companies"
        />
        <CompaniesGrid companies={featuredCompanies} loading={featuredCompanies.length === 0} />
      </section>

      <ToolsSection />
    </>
  );
}