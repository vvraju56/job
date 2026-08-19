import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BadgeCheck, Building2, ExternalLink, Globe, MapPin, Users } from "lucide-react";
import Link from "next/link";

import { JobsGrid } from "@/components/jobs/jobs-grid";
import { Badge, GlassCard } from "@/components/ui/badge";
import { serverApi } from "@/lib/server-api";
import { formatNumber } from "@/lib/utils";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  try {
    const company = await serverApi.company(slug);
    return {
      title: company.name,
      description:
        company.description ??
        `${company.name} — ${company.industry ?? "company"} with ${company.open_positions} open positions on Makeable Jobs.`,
      openGraph: {
        title: `${company.name} | Makeable Jobs`,
        description: company.description ?? undefined,
      },
    };
  } catch {
    return { title: "Company not found" };
  }
}

export default async function CompanyDetailPage({ params }: PageProps) {
  const { slug } = await params;
  let company;
  let jobList;
  try {
    company = await serverApi.company(slug);
    jobList = await serverApi.companyJobs(company.name, 20);
  } catch {
    notFound();
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <nav className="mb-6 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-primary">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/companies" className="hover:text-primary">Companies</Link>
        <span className="mx-2">/</span>
        <span className="text-white">{company.name}</span>
      </nav>

      <GlassCard className="mb-10 p-6 sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-white/5">
            {company.logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={company.logo}
                alt={`${company.name} logo`}
                className="h-full w-full object-contain p-2"
              />
            ) : (
              <Building2 className="h-9 w-9 text-primary" />
            )}
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
                {company.name}
              </h1>
              {company.verified && (
                <Badge className="border-success/30 bg-success/10 text-success">
                  <BadgeCheck className="h-3 w-3" /> Verified
                </Badge>
              )}
            </div>
            {company.description && (
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {company.description}
              </p>
            )}
            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
              {company.industry && (
                <span className="flex items-center gap-1.5">
                  <Building2 className="h-4 w-4 text-accent" /> {company.industry}
                </span>
              )}
              {company.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-accent" /> {company.location}
                </span>
              )}
              {company.size && (
                <span className="flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-accent" /> {company.size}
                </span>
              )}
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-primary hover:text-accent"
                >
                  <Globe className="h-4 w-4" /> {company.website.replace(/^https?:\/\//, "")}
                </a>
              )}
            </div>
          </div>
          <div className="flex shrink-0 gap-8 sm:flex-col sm:items-end">
            <div className="text-center">
              <p className="text-3xl font-extrabold text-primary">
                {company.open_positions}
              </p>
              <p className="text-xs text-muted-foreground">open positions</p>
            </div>
            {company.rating > 0 && (
              <div className="text-center">
                <p className="text-3xl font-extrabold text-accent">{company.rating}</p>
                <p className="text-xs text-muted-foreground">
                  {formatNumber(company.review_count)} reviews
                </p>
              </div>
            )}
          </div>
        </div>
      </GlassCard>

      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold">Open positions at {company.name}</h2>
        {company.website && (
          <a
            href={company.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-accent"
          >
            Visit website <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>
      <JobsGrid jobs={jobList.items} loading={jobList.items.length === 0} />
    </div>
  );
}