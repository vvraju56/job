"use client";

import { useCallback, useEffect, useState } from "react";

import { jobsService, usersService } from "@/lib/services";
import type { Job } from "@/lib/types";

export function useSavedJobs() {
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshSaved = useCallback(async () => {
    try {
      const jobs = await usersService.savedJobs();
      setSavedJobs(jobs);
      setSavedIds(new Set(jobs.map((j) => j.id)));
    } catch {
      setSavedJobs([]);
      setSavedIds(new Set());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSaved();
  }, [refreshSaved]);

  const toggleSave = useCallback(
    async (job: Job) => {
      const currentlySaved = savedIds.has(job.id);
      if (currentlySaved) {
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(job.id);
          return next;
        });
        setSavedJobs((prev) => prev.filter((j) => j.id !== job.id));
        try {
          await jobsService.unsave(job.id);
        } catch {
          void refreshSaved();
        }
      } else {
        setSavedIds((prev) => new Set(prev).add(job.id));
        try {
          await jobsService.save(job.id);
        } catch {
          void refreshSaved();
        }
      }
    },
    [savedIds, refreshSaved],
  );

  const isSaved = useCallback((id: string) => savedIds.has(id), [savedIds]);

  return { savedJobs, savedIds, loading, toggleSave, isSaved, refreshSaved };
}