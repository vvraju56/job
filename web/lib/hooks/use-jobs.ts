"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { jobsService } from "@/lib/services";
import type { Job, SearchFilters } from "@/lib/types";

interface UseJobsOptions {
  initialFilters?: SearchFilters;
  pageSize?: number;
}

export function useJobs({ initialFilters = {}, pageSize = 20 }: UseJobsOptions = {}) {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const requestId = useRef(0);

  const loadFirstPage = useCallback(
    async (nextFilters: SearchFilters) => {
      const id = ++requestId.current;
      setLoading(true);
      setError(null);
      try {
        const result = await jobsService.search({
          ...nextFilters,
          page: 1,
          page_size: pageSize,
        });
        if (id !== requestId.current) return;
        setJobs(result.items);
        setTotal(result.total);
        setPage(1);
        setHasMore(result.items.length < result.total);
      } catch (err) {
        if (id !== requestId.current) return;
        setError(err instanceof Error ? err.message : "Failed to load jobs");
      } finally {
        if (id === requestId.current) setLoading(false);
      }
    },
    [pageSize],
  );

  const loadMore = useCallback(async () => {
    if (loading || loadingMore || !hasMore) return;
    const nextPage = page + 1;
    setLoadingMore(true);
    try {
      const result = await jobsService.search({
        ...filters,
        page: nextPage,
        page_size: pageSize,
      });
      setJobs((prev) => {
        const merged = [...prev, ...result.items];
        setHasMore(merged.length < result.total);
        return merged;
      });
      setPage(nextPage);
    } catch {
      setHasMore(false);
    } finally {
      setLoadingMore(false);
    }
  }, [filters, loading, loadingMore, hasMore, page, pageSize]);

  useEffect(() => {
    void loadFirstPage(filters);
  }, [loadFirstPage, filters]);

  const updateFilters = useCallback((next: SearchFilters) => {
    setFilters((prev) => ({ ...prev, ...next }));
  }, []);

  return {
    jobs,
    total,
    loading,
    loadingMore,
    error,
    hasMore,
    loadMore,
    updateFilters,
    filters,
    setFilters,
    retry: () => loadFirstPage(filters),
  };
}