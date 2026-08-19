"use client";

import { useCallback, useEffect, useState } from "react";

import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { GlassCard } from "@/components/ui/badge";
import { useSavedJobs } from "@/lib/hooks/use-saved-jobs";

export default function SavedJobsPage() {
  const { savedJobs, loading, refreshSaved } = useSavedJobs();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Saved Jobs</h2>
          <p className="text-sm text-muted-foreground">
            {savedJobs.length} saved {savedJobs.length === 1 ? "job" : "jobs"}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <JobCardSkeleton key={i} />
          ))}
        </div>
      ) : savedJobs.length === 0 ? (
        <GlassCard className="p-12 text-center">
          <p className="text-lg font-semibold">No saved jobs yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Tap the bookmark icon on any job to save it here.
          </p>
        </GlassCard>
      ) : (
        <div className="grid gap-4">
          {savedJobs.map((job, i) => (
            <JobCard key={job.id} job={job} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}