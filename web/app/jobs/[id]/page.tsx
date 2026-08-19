import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  BadgeCheck,
  Building2,
  Clock,
  ExternalLink,
  MapPin,
  Wifi,
} from "lucide-react";
import Link from "next/link";

import { ApplyButton } from "@/components/jobs/apply-button";
import { JobCard, LogoImage } from "@/components/jobs/job-card";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/badge";
import { SectionHeading } from "@/components/ui/section-heading";
import { serverApi } from "@/lib/server-api";
import { formatSalary, timeAgo } from "@/lib/utils";
import { SOURCE_LABELS } from "@/lib/types";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  try {
    const job = await serverApi.job(id);
    return {
      title: job.title,
      description: `${job.title} at ${job.company_name}${job.location ? ` in ${job.location}` : ""}. Apply on the original website.`,
      openGraph: {
        title: `${job.title} at ${job.company_name}`,
        description: `${job.title} — ${formatSalary(job)}. Apply on the original website.`,
        type: "article",
      },
    };
  } catch {
    return { title: "Job not found" };
  }
}

export default async function JobDetailPage({ params }: PageProps) {
  const { id } = await params;
  let job;
  let similar: Awaited<ReturnType<typeof serverApi.similarJobs>> = [];
  try {
    job = await serverApi.job(id);
    similar = await serverApi.similarJobs(id).catch(() => []);
  } catch {
    notFound();
  }

  const jobJsonLd = {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    title: job.title,
    description: job.description ?? job.title,
    datePosted: job.posted_at ?? new Date().toISOString(),
    hiringOrganization: {
      "@type": "Organization",
      name: job.company_name,
      logo: job.company_logo ?? undefined,
    },
    jobLocation: job.remote
      ? { "@type": "Place" }
      : {
          "@type": "Place",
          address: { "@type": "PostalAddress", addressLocality: job.location },
        },
    employmentType:
      job.job_type === "full_time" ? "FULL_TIME" : job.job_type.toUpperCase().replace("_", "-"),
    ...(job.salary_min != null || job.salary_max != null
      ? {
          baseSalary: {
            "@type": "MonetaryAmount",
            currency: job.salary_currency,
            value: {
              "@type": "QuantitativeValue",
              ...(job.salary_min != null ? { minValue: job.salary_min } : {}),
              ...(job.salary_max != null ? { maxValue: job.salary_max } : {}),
            },
          },
        }
      : {}),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jobJsonLd) }}
      />

      <div className="relative overflow-hidden">
        <div className="bg-hero-glow pointer-events-none absolute inset-0" />
        <div className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6">
          <nav className="mb-6 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <Link href="/jobs" className="hover:text-primary">Jobs</Link>
            <span className="mx-2">/</span>
            <span className="text-white">{job.title}</span>
          </nav>

          <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
            <div className="min-w-0">
              <GlassCard className="p-6 sm:p-8">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <Link
                      href={`/companies/${job.company_id ?? job.company_name}`}
                      className="shrink-0"
                    >
                      <span className="relative block">
                        <LogoImage src={job.company_logo} name={job.company_name} className="h-16 w-16" />
                        {job.company_id && (
                          <span className="absolute -right-1 -bottom-1 flex h-5 w-5 items-center justify-center rounded-full bg-secondary ring-2 ring-background">
                            <BadgeCheck className="h-3 w-3 text-white" />
                          </span>
                        )}
                      </span>
                    </Link>
                    <div>
                      <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
                        {job.title}
                      </h1>
                      <p className="mt-1 flex items-center gap-2 text-muted-foreground">
                        <Building2 className="h-4 w-4" />
                        <Link
                          href={`/companies/${job.company_id ?? job.company_name}`}
                          className="hover:text-primary"
                        >
                          {job.company_name}
                        </Link>
                      </p>
                    </div>
                  </div>
                  <Badge className="border-primary/30 bg-primary/10 text-primary text-sm px-3 py-1">
                    {SOURCE_LABELS[job.source] ?? job.apply_on}
                  </Badge>
                </div>

                <div className="mt-6 flex flex-wrap gap-x-6 gap-y-3 text-sm text-muted-foreground">
                  {job.location && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-4 w-4 text-accent" /> {job.location}
                    </span>
                  )}
                  {job.remote && (
                    <span className="flex items-center gap-1.5 text-success">
                      <Wifi className="h-4 w-4" /> Remote
                    </span>
                  )}
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-4 w-4 text-accent" /> Posted {timeAgo(job.posted_at)}
                  </span>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge className="border-primary/30 bg-primary/10 text-primary text-sm">
                    {formatSalary(job)}
                  </Badge>
                  <Badge className="capitalize text-sm">{job.job_type.replace("_", " ")}</Badge>
                  <Badge className="capitalize text-sm">{job.level}</Badge>
                  {job.experience_max > 0 && (
                    <Badge className="text-sm">
                      {job.experience_min}–{job.experience_max} yrs exp
                    </Badge>
                  )}
                </div>

                <div className="mt-8">
                  <h2 className="mb-3 text-lg font-semibold">About the job</h2>
                  <div className="prose-invert space-y-3 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                    {job.description ?? "No description provided for this listing."}
                  </div>
                </div>

                {job.skills.length > 0 && (
                  <div className="mt-8">
                    <h2 className="mb-3 text-lg font-semibold">Required skills</h2>
                    <div className="flex flex-wrap gap-2">
                      {job.skills.map((skill) => (
                        <Badge key={skill} className="border-primary/20 bg-white/5 text-sm text-accent">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-muted-foreground">
                  <p>
                    <strong className="text-white">Important:</strong> This job is aggregated
                    from <strong className="text-accent">{job.apply_on}</strong>. Makeable Jobs
                    does not own or host this listing. Click{" "}
                    <strong className="text-white">Apply on {job.apply_on}</strong> to apply on
                    the original website.
                  </p>
                </div>
              </GlassCard>
            </div>

            <div className="space-y-6">
              <div className="lg:sticky lg:top-20">
                <GlassCard className="p-6">
                  <h2 className="mb-4 text-lg font-semibold">Ready to apply?</h2>
                  <ApplyButton job={job} />
                  <p className="mt-3 flex items-start gap-2 text-xs text-muted-foreground">
                    <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    You&apos;ll be redirected to the original job portal to complete your
                    application.
                  </p>
                </GlassCard>
              </div>
            </div>
          </div>
        </div>
      </div>

      {similar.length > 0 && (
        <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6">
          <SectionHeading eyebrow="You might also like" title="Similar Jobs" />
          <div className="grid gap-5 md:grid-cols-2">
            {similar.map((s, i) => (
              <JobCard key={s.id} job={s} index={i} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}