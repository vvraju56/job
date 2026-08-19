"use client";

import { motion } from "framer-motion";
import { BadgeCheck, Building2, Check, Clock, MapPin, Share2, Wifi } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { SaveButton } from "@/components/jobs/save-button";
import { Badge } from "@/components/ui/badge";
import { cn, formatSalary, initials, timeAgo } from "@/lib/utils";
import { SOURCE_COLORS, SOURCE_LABELS } from "@/lib/types";
import type { Job } from "@/lib/types";

function ShareButton({ job }: { job: Job }) {
  const [copied, setCopied] = useState(false);

  const share = async () => {
    const url = `${window.location.origin}/jobs/${job.id}`;
    try {
      if (navigator.share) {
        await navigator.share({
          title: job.title,
          text: `${job.title} at ${job.company_name}`,
          url,
        });
        return;
      }
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      try {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      } catch {
        /* clipboard unavailable */
      }
    }
  };

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        void share();
      }}
      className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-muted-foreground transition-colors hover:bg-white/10 hover:text-white"
      aria-label={copied ? "Link copied" : "Share job"}
      title={copied ? "Link copied" : "Share job"}
    >
      {copied ? <Check className="h-4 w-4 text-success" /> : <Share2 className="h-4 w-4" />}
    </button>
  );
}

export function LogoImage({
  src,
  name,
  className,
}: {
  src?: string | null;
  name: string;
  className?: string;
}) {
  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt={`${name} logo`}
        loading="lazy"
        className={cn(
          "h-12 w-12 rounded-xl border border-white/10 bg-white/5 object-contain p-1.5",
          className,
        )}
        onError={(e) => {
          const el = e.currentTarget;
          el.style.display = "none";
          el.nextElementSibling?.classList.remove("hidden");
        }}
      />
    );
  }
  return (
    <span
      className={cn(
        "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/80 to-secondary/80 text-sm font-bold text-white",
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}

export function JobCard({
  job,
  index = 0,
}: {
  job: Job;
  index?: number;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.04, 0.4) }}
      className="group glass card-hover relative rounded-2xl p-5"
    >
      <div className="flex items-start gap-4">
        <Link href={`/companies/${job.company_id ?? job.company_name}`} className="shrink-0">
          <span className="relative block">
            {job.company_logo ? (
              <img
                src={job.company_logo}
                alt={`${job.company_name} logo`}
                loading="lazy"
                className="h-12 w-12 rounded-xl border border-white/10 bg-white/5 object-contain p-1.5"
              />
            ) : (
              <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/80 to-secondary/80 text-sm font-bold">
                {initials(job.company_name)}
              </span>
            )}
            {job.company_id ? (
              <span className="absolute -right-1 -bottom-1 flex h-4 w-4 items-center justify-center rounded-full bg-secondary ring-2 ring-background">
                <BadgeCheck className="h-3 w-3 text-white" />
              </span>
            ) : null}
          </span>
        </Link>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <Link
                href={`/jobs/${job.id}`}
                className="line-clamp-1 text-base font-semibold transition-colors group-hover:text-primary"
              >
                {job.title}
              </Link>
              <p className="mt-0.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                <Building2 className="h-3.5 w-3.5" />
                <span className="truncate">{job.company_name}</span>
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              <ShareButton job={job} />
              <SaveButton job={job} />
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-muted-foreground">
            {job.location && (
              <span className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-accent" />
                {job.location}
              </span>
            )}
            {job.remote && (
              <span className="flex items-center gap-1.5 text-success">
                <Wifi className="h-3.5 w-3.5" />
                Remote
              </span>
            )}
            {job.posted_at && (
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                {timeAgo(job.posted_at)}
              </span>
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            {formatSalary(job) !== "Not disclosed" && (
              <Badge className="border-primary/30 bg-primary/10 text-primary">
                {formatSalary(job)}
              </Badge>
            )}
            <Badge className="capitalize">{job.job_type.replace("_", " ")}</Badge>
            <Badge className="capitalize">{job.level}</Badge>
            {job.source in SOURCE_COLORS ? (
              <Badge className={SOURCE_COLORS[job.source as keyof typeof SOURCE_COLORS]}>
                {SOURCE_LABELS[job.source]}
              </Badge>
            ) : (
              <Badge className="border-white/10 text-accent">{job.apply_on}</Badge>
            )}
          </div>
        </div>
      </div>
    </motion.article>
  );
}

export function JobCardSkeleton() {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <div className="animate-shimmer h-12 w-12 rounded-xl" />
        <div className="flex-1 space-y-3">
          <div className="animate-shimmer h-4 w-2/3 rounded" />
          <div className="animate-shimmer h-3 w-1/3 rounded" />
          <div className="animate-shimmer h-3 w-1/2 rounded" />
        </div>
      </div>
    </div>
  );
}