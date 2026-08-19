"use client";

import { useSearchParams } from "next/navigation";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Suspense, useEffect, useRef, useState } from "react";

import { JobFilters } from "@/components/jobs/job-filters";
import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { useJobs } from "@/lib/hooks/use-jobs";
import { cn } from "@/lib/utils";
import type { SearchFilters } from "@/lib/types";

function JobsPageInner() {
  const searchParams = useSearchParams();
  const initial: SearchFilters = {
    q: searchParams.get("q") ?? undefined,
    location: searchParams.get("location") ?? undefined,
    remote: searchParams.get("remote") === "true" ? true : undefined,
    sort: (searchParams.get("sort") as SearchFilters["sort"]) ?? "recent",
  };
  const { jobs, total, loading, loadingMore, error, hasMore, loadMore, updateFilters, filters } =
    useJobs({ initialFilters: initial, pageSize: 20 });

  const [query, setQuery] = useState(initial.q ?? "");
  const [showFilters, setShowFilters] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) void loadMore();
      },
      { rootMargin: "300px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore]);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilters({ q: query || undefined, page: 1 });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight">Browse Jobs</h1>
        <p className="mt-2 text-muted-foreground">
          {loading ? "Searching across sources…" : `${total.toLocaleString()} opportunities found`}
        </p>
      </div>

      <form onSubmit={onSearch} className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title, skill, or company"
            className="pl-11"
          />
        </div>
        <div className="flex gap-3">
          <Select
            value={filters.sort ?? "recent"}
            onChange={(e) =>
              updateFilters({ sort: e.target.value as SearchFilters["sort"], page: 1 })
            }
            className="sm:w-48"
          >
            <option value="recent">Most recent</option>
            <option value="salary_desc">Highest salary</option>
            <option value="salary_asc">Lowest salary</option>
            <option value="relevance">Relevance</option>
          </Select>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowFilters((v) => !v)}
            className="sm:hidden"
            aria-label="Toggle filters"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </form>

      <div className="grid gap-8 lg:grid-cols-[280px_1fr]">
        <aside
          className={cn(
            "lg:sticky lg:top-20 lg:block lg:h-[calc(100vh-6rem)] lg:overflow-y-auto",
            showFilters ? "block" : "hidden",
          )}
        >
          <div className="glass rounded-2xl p-5">
            <div className="mb-3 flex items-center justify-between lg:hidden">
              <h3 className="text-sm font-semibold">Filters</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5"
                aria-label="Close filters"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <JobFilters
              filters={filters}
              onApply={(next) => {
                updateFilters(next);
                setShowFilters(false);
              }}
            />
          </div>
        </aside>

        <div>
          {error && (
            <div className="glass mb-4 flex flex-col items-center gap-3 rounded-2xl border-warning/30 p-6 text-center">
              <p className="text-warning">{error}</p>
              <Button variant="outline" size="sm" onClick={() => updateFilters({ ...filters })}>
                Retry
              </Button>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {jobs.map((job, i) => (
              <JobCard key={job.id} job={job} index={i} />
            ))}
            {loading && Array.from({ length: 6 }).map((_, i) => <JobCardSkeleton key={i} />)}
          </div>

          {!loading && jobs.length === 0 && (
            <div className="glass rounded-2xl p-12 text-center">
              <p className="text-lg font-semibold">No jobs found</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Try adjusting your search or clearing filters.
              </p>
            </div>
          )}

          {loadingMore && (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <JobCardSkeleton key={i} />
              ))}
            </div>
          )}
          <div ref={sentinelRef} className="h-px" />
        </div>
      </div>
    </div>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-muted-foreground">Loading…</div>}>
      <JobsPageInner />
    </Suspense>
  );
}