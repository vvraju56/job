"use client";

import { Building2, ExternalLink, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { GlassCard } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { usersService } from "@/lib/services";
import { APP_STATUS_LABELS, type AppStatus, type Application } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

const STATUS_COLORS: Record<AppStatus, string> = {
  applied: "border-primary/40 bg-primary/10 text-primary",
  interviewing: "border-warning/40 bg-warning/10 text-warning",
  offered: "border-success/40 bg-success/10 text-success",
  rejected: "border-red-500/40 bg-red-500/10 text-red-400",
  withdrawn: "border-white/15 bg-white/5 text-muted-foreground",
};

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[] | null>(null);
  const [filter, setFilter] = useState<AppStatus | "">("");

  const load = useCallback(async (status?: AppStatus) => {
    setApps(null);
    try {
      setApps(await usersService.applications(status));
    } catch {
      setApps([]);
    }
  }, []);

  useEffect(() => {
    void load(filter || undefined);
  }, [filter, load]);

  const updateStatus = async (app: Application, status: AppStatus) => {
    await usersService.updateApplication(app.id, status);
    void load(filter || undefined);
  };

  const remove = async (app: Application) => {
    await usersService.deleteApplication(app.id);
    void load(filter || undefined);
  };

  const activeCount = apps?.filter((a) => ["applied", "interviewing"].includes(a.status)).length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Applications</h2>
          <p className="text-sm text-muted-foreground">
            Track every role you&apos;ve applied to through Makeable Jobs.
          </p>
        </div>
        <Select
          value={filter}
          onChange={(e) => setFilter(e.target.value as AppStatus | "")}
          className="w-48"
        >
          <option value="">All statuses</option>
          {(Object.keys(APP_STATUS_LABELS) as AppStatus[]).map((s) => (
            <option key={s} value={s}>
              {APP_STATUS_LABELS[s]}
            </option>
          ))}
        </Select>
      </div>

      {activeCount > 0 && (
        <p className="rounded-xl border border-success/30 bg-success/10 px-4 py-2.5 text-sm text-success">
          {activeCount} active {activeCount === 1 ? "application" : "applications"} — keep the
          momentum going!
        </p>
      )}

      {apps === null ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-shimmer glass h-28 rounded-2xl" />
          ))}
        </div>
      ) : apps.length === 0 ? (
        <GlassCard className="p-12 text-center">
          <p className="text-lg font-semibold">No applications tracked yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            When you apply through Makeable Jobs, applications are tracked here
            automatically.
          </p>
        </GlassCard>
      ) : (
        <div className="space-y-4">
          {apps.map((app) => (
            <GlassCard key={app.id} className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-semibold">{app.role ?? "Application"}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Building2 className="h-3.5 w-3.5" />
                    {app.company_name ?? "Unknown company"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Applied {timeAgo(app.applied_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn("rounded-full border px-3 py-1 text-xs font-medium", STATUS_COLORS[app.status])}>
                    {APP_STATUS_LABELS[app.status]}
                  </span>
                  <Select
                    value={app.status}
                    onChange={(e) => updateStatus(app, e.target.value as AppStatus)}
                    className="h-9 w-36 text-xs"
                    aria-label="Update status"
                  >
                    {(Object.keys(APP_STATUS_LABELS) as AppStatus[]).map((s) => (
                      <option key={s} value={s}>
                        {APP_STATUS_LABELS[s]}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-3 border-t border-white/10 pt-3">
                {app.applied_url && (
                  <a
                    href={app.applied_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-accent"
                  >
                    <ExternalLink className="h-3.5 w-3.5" /> View original
                  </a>
                )}
                {app.notes && <p className="text-xs text-muted-foreground">Note: {app.notes}</p>}
                <Button
                  variant="ghost"
                  size="iconSm"
                  onClick={() => remove(app)}
                  className="ml-auto text-red-400 hover:bg-red-500/10 hover:text-red-400"
                  aria-label="Delete application"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}