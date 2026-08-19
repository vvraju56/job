import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import type { Job } from "@/lib/types";

export function JobsGrid({
  jobs,
  loading = false,
  emptyMessage = "No jobs found. Try a different search.",
}: {
  jobs: Job[];
  loading?: boolean;
  emptyMessage?: string;
}) {
  if (loading) {
    return (
      <div className="grid gap-5 md:grid-cols-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <JobCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="glass rounded-2xl p-10 text-center text-muted-foreground">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      {jobs.map((job, i) => (
        <JobCard key={job.id} job={job} index={i} />
      ))}
    </div>
  );
}