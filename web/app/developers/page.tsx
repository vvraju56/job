"use client";

import {
  Activity,
  Database,
  Gauge,
  HeartPulse,
  Server,
  ShieldAlert,
  Timer,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { RequireAuth } from "@/components/tools/require-auth";
import { GlassCard } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { developerService } from "@/lib/services";
import type { Usage } from "@/lib/types";

function DevelopersDashboard() {
  const { user } = useAuth();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await developerService.usage();
      setUsage(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load API usage");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (user?.role !== "admin") {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <ShieldAlert className="mx-auto h-12 w-12 text-warning" />
        <h1 className="mt-4 text-2xl font-bold">Admin access required</h1>
        <p className="mt-2 text-muted-foreground">
          The Developer API Dashboard is restricted to administrators.
        </p>
      </div>
    );
  }

  const limit = usage?.monthly_limit ?? 0;
  const used = usage?.searches_used ?? 0;
  const usedPct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const hitRate = usage?.cache_hit_rate ?? 0;

  const statCards = [
    {
      label: "Searches Used",
      value: used.toLocaleString(),
      icon: Activity,
      tone: "text-primary",
    },
    {
      label: "Monthly Limit",
      value: limit.toLocaleString(),
      icon: Gauge,
      tone: "text-muted-foreground",
    },
    {
      label: "Remaining",
      value: (usage?.remaining ?? 0).toLocaleString(),
      icon: Timer,
      tone: "text-success",
    },
    {
      label: "Cache Hit %",
      value: `${hitRate}%`,
      icon: Database,
      tone: "text-accent",
    },
  ];

  const refresh = async () => {
    setRefreshing(true);
    try {
      await load();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Developer API Dashboard</h1>
          <p className="mt-1 text-muted-foreground">
            SerpApi Google Jobs search usage, cache health and provider status.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void refresh()} disabled={refreshing}>
          Refresh
        </Button>
      </div>

      {error && (
        <div className="glass mb-6 flex items-center justify-between rounded-2xl border-warning/30 p-4 text-warning">
          <p className="text-sm">{error}</p>
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <GlassCard key={card.label} className="p-5">
            <card.icon className={`h-5 w-5 ${card.tone}`} />
            <p className="mt-3 text-2xl font-extrabold">{card.value}</p>
            <p className="text-xs text-muted-foreground">{card.label}</p>
          </GlassCard>
        ))}
      </div>

      <GlassCard className="mt-6 p-6">
        <h2 className="mb-2 flex items-center gap-2 font-bold">
          <Activity className="h-5 w-5 text-primary" /> Search quota — this month
        </h2>
        <p className="mb-3 text-sm text-muted-foreground">
          {used} of {limit} SerpApi searches used ({usedPct}%). Non-cached searches consume quota.
        </p>
        <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary to-accent transition-all"
            style={{ width: `${Math.max(usedPct, used > 0 ? 2 : 0)}%` }}
          />
        </div>
      </GlassCard>

      <div className="mt-6 grid gap-8 lg:grid-cols-2">
        <GlassCard className="p-6">
          <h2 className="mb-4 flex items-center gap-2 font-bold">
            <Database className="h-5 w-5 text-accent" /> Cache statistics
          </h2>
          <div className="space-y-3">
            {[
              { label: "Backend", value: usage?.cache.backend ?? "memory" },
              { label: "Cached entries", value: usage?.cache.entries.toLocaleString() ?? "0" },
              { label: "Cache hits", value: usage?.cache.hits.toLocaleString() ?? "0" },
              { label: "Cache misses", value: usage?.cache.misses.toLocaleString() ?? "0" },
              { label: "Hit rate", value: `${usage?.cache.hit_rate ?? 0}%` },
            ].map((row) => (
              <div
                key={row.label}
                className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm"
              >
                <span className="text-muted-foreground">{row.label}</span>
                <span className="font-semibold">{row.value}</span>
              </div>
            ))}
          </div>

          <h2 className="mb-4 mt-8 flex items-center gap-2 font-bold">
            <HeartPulse className="h-5 w-5 text-success" /> API health
          </h2>
          <div className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-3">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                usage?.provider.configured ? "bg-success" : "bg-warning"
              }`}
            />
            <span className="text-sm font-medium">
              Provider: {usage?.provider.name ?? "—"}
            </span>
            <span className="ml-auto text-xs text-muted-foreground">
              {usage?.provider.configured ? "Configured" : "Not configured (DB fallback)"}
            </span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            <Server className="mr-1 inline h-3.5 w-3.5" />
            Total logged requests: {usage?.total_requests.toLocaleString() ?? "0"}
          </p>
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="mb-4 flex items-center gap-2 font-bold">
            <Timer className="h-5 w-5 text-warning" /> Recent searches
          </h2>
          <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
            {usage?.recent_searches.length ? (
              usage.recent_searches.map((log) => (
                <div
                  key={`${log.timestamp}-${log.query}`}
                  className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2 text-sm"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">
                      {log.query || "—"}
                      {log.location ? (
                        <span className="text-muted-foreground"> · {log.location}</span>
                      ) : null}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {log.endpoint} · page {log.page} · {log.response_time_ms}ms
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        log.cached
                          ? "bg-success/15 text-success"
                          : "bg-white/5 text-muted-foreground"
                      }`}
                    >
                      {log.cached ? "CACHED" : "LIVE"}
                    </span>
                    {log.status_code >= 400 && (
                      <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[10px] font-semibold text-warning">
                        {log.status_code}
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No searches yet — results appear once users search.
              </p>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

export default function DevelopersPage() {
  return (
    <RequireAuth>
      <DevelopersDashboard />
    </RequireAuth>
  );
}