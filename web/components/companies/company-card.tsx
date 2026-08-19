"use client";

import { motion } from "framer-motion";
import { BadgeCheck, Building2, ExternalLink, MapPin } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { cn, formatNumber } from "@/lib/utils";
import type { Company } from "@/lib/types";

export function CompanyCard({
  company,
  index = 0,
}: {
  company: Company;
  index?: number;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.05, 0.4) }}
      className="group glass card-hover rounded-2xl p-6"
    >
      <div className="flex items-center justify-between">
        <Link
          href={`/companies/${company.slug}`}
          className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-white/5"
        >
          {company.logo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={company.logo}
              alt={`${company.name} logo`}
              loading="lazy"
              className="h-full w-full object-contain p-2"
            />
          ) : (
            <Building2 className="h-6 w-6 text-primary" />
          )}
        </Link>
        {company.verified && (
          <Badge className="border-success/30 bg-success/10 text-success">
            <BadgeCheck className="h-3 w-3" /> Verified
          </Badge>
        )}
      </div>

      <Link href={`/companies/${company.slug}`}>
        <h3 className="mt-4 text-lg font-semibold transition-colors group-hover:text-primary">
          {company.name}
        </h3>
      </Link>
      <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
        {company.description ?? `${company.industry ?? "Company"} looking for talent.`}
      </p>

      <div className="mt-4 space-y-1.5 text-sm text-muted-foreground">
        {company.location && (
          <p className="flex items-center gap-2">
            <MapPin className="h-3.5 w-3.5 text-accent" /> {company.location}
          </p>
        )}
        {company.industry && (
          <p className="flex items-center gap-2">
            <Building2 className="h-3.5 w-3.5 text-accent" /> {company.industry}
          </p>
        )}
      </div>

      <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
        <span className="flex items-center gap-2">
          <span className="text-lg font-bold text-primary">
            {company.open_positions}
          </span>
          <span className="text-xs text-muted-foreground">
            open {company.open_positions === 1 ? "position" : "positions"}
          </span>
        </span>
        {company.website && (
          <a
            href={company.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-primary"
          >
            <ExternalLink className="h-3.5 w-3.5" /> Website
          </a>
        )}
      </div>
    </motion.article>
  );
}

export function CompanyCardSkeleton() {
  return (
    <div className="glass rounded-2xl p-6">
      <div className="animate-shimmer h-14 w-14 rounded-2xl" />
      <div className="animate-shimmer mt-4 h-4 w-1/2 rounded" />
      <div className="animate-shimmer mt-2 h-3 w-full rounded" />
      <div className="animate-shimmer mt-5 h-4 w-1/3 rounded" />
    </div>
  );
}