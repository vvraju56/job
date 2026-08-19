"use client";

import { Bell, BellOff, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { GlassCard } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { notificationsService } from "@/lib/services";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [query, setQuery] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setAlerts(await notificationsService.alerts());
    } catch {
      setAlerts([]);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await notificationsService.createAlert({
        query: query.trim(),
        frequency,
        filters: {},
      });
      setQuery("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create alert");
    } finally {
      setCreating(false);
    }
  };

  const remove = async (alert: Alert) => {
    await notificationsService.deleteAlert(alert.id);
    await load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Job Alerts</h2>
        <p className="text-sm text-muted-foreground">
          Get notified by email and push when new jobs match your search.
        </p>
      </div>

      <form onSubmit={create} className="glass flex flex-col gap-3 rounded-2xl p-5 sm:flex-row">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Flutter Developer, Remote Jobs, Chennai Jobs"
          className="flex-1"
        />
        <Select
          value={frequency}
          onChange={(e) => setFrequency(e.target.value)}
          className="sm:w-40"
        >
          <option value="instant">Instant</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </Select>
        <Button type="submit" disabled={creating || !query.trim()}>
          <Bell className="h-4 w-4" /> Create alert
        </Button>
      </form>

      {error && (
        <p className="rounded-xl border border-warning/30 bg-warning/10 px-4 py-2.5 text-sm text-warning">
          {error}
        </p>
      )}

      {alerts === null ? (
        <div className="space-y-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="animate-shimmer glass h-20 rounded-2xl" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <GlassCard className="p-12 text-center">
          <p className="text-lg font-semibold">No alerts yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first alert to never miss a matching job.
          </p>
        </GlassCard>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <GlassCard key={alert.id} className="flex items-center justify-between gap-4 p-5">
              <div className="flex items-center gap-4">
                <span
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                    alert.active ? "bg-primary/15 text-primary" : "bg-white/5 text-muted-foreground"
                  }`}
                >
                  {alert.active ? <Bell className="h-5 w-5" /> : <BellOff className="h-5 w-5" />}
                </span>
                <div>
                  <p className="font-semibold">{alert.query}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {alert.frequency} digest · {alert.active ? "active" : "paused"}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="iconSm"
                onClick={() => remove(alert)}
                className="text-red-400 hover:bg-red-500/10 hover:text-red-400"
                aria-label="Delete alert"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}