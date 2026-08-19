"use client";

import {
  Bookmark,
  Briefcase,
  Building2,
  Megaphone,
  Search,
  ShieldAlert,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { RequireAuth } from "@/components/tools/require-auth";
import { GlassCard } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import { adminService } from "@/lib/services";
import type { Analytics, User } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

function AdminPanel() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [usersList, setUsersList] = useState<User[]>([]);
  const [broadcastTitle, setBroadcastTitle] = useState("");
  const [broadcastBody, setBroadcastBody] = useState("");
  const [broadcastResult, setBroadcastResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [a, u] = await Promise.all([adminService.analytics(), adminService.users(50)]);
      setAnalytics(a);
      setUsersList(u);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load admin data");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleRole = async (target: User) => {
    await adminService.setRole(target.id, target.role === "admin" ? "user" : "admin");
    await load();
  };

  const broadcast = async () => {
    if (!broadcastTitle.trim()) return;
    try {
      const res = await adminService.broadcast(
        broadcastTitle.trim(),
        broadcastBody.trim() || undefined,
      );
      setBroadcastResult(`Notification sent to ${res.sent} users.`);
      setBroadcastTitle("");
      setBroadcastBody("");
    } catch (err) {
      setBroadcastResult(null);
      setError(err instanceof Error ? err.message : "Broadcast failed");
    }
  };

  if (user?.role !== "admin") {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <ShieldAlert className="mx-auto h-12 w-12 text-warning" />
        <h1 className="mt-4 text-2xl font-bold">Admin access required</h1>
        <p className="mt-2 text-muted-foreground">
          You don&apos;t have permission to view this page.
        </p>
      </div>
    );
  }

  const statCards = analytics
    ? [
        { label: "Active Users", value: analytics.active_users, icon: Users },
        { label: "Live Jobs", value: analytics.total_jobs, icon: Briefcase },
        { label: "Total Searches", value: analytics.total_searches, icon: Search },
        { label: "Saved Jobs", value: analytics.total_saved_jobs, icon: Bookmark },
        { label: "Applications", value: analytics.total_applications, icon: Users },
      ]
    : [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight">Admin Panel</h1>
        <p className="mt-1 text-muted-foreground">
          Platform analytics, user management, notifications and moderation.
        </p>
      </div>

      {error && (
        <div className="glass mb-6 flex items-center justify-between rounded-2xl border-warning/30 p-4 text-warning">
          <p className="text-sm">{error}</p>
          <Button variant="outline" size="sm" onClick={load}>
            Retry
          </Button>
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((card) => (
          <GlassCard key={card.label} className="p-5">
            <card.icon className="h-5 w-5 text-primary" />
            <p className="mt-3 text-2xl font-extrabold">{formatNumber(card.value)}</p>
            <p className="text-xs text-muted-foreground">{card.label}</p>
          </GlassCard>
        ))}
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <GlassCard className="p-6">
          <h2 className="mb-4 flex items-center gap-2 font-bold">
            <Building2 className="h-5 w-5 text-primary" /> Popular companies
          </h2>
          <div className="space-y-3">
            {analytics?.popular_companies.map((c, i) => (
              <div key={c.name} className="flex items-center gap-3">
                <span className="w-6 text-sm text-muted-foreground">{i + 1}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{c.name}</span>
                    <span className="text-muted-foreground">{c.count} jobs</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                      style={{
                        width: `${Math.min(100, (c.count / Math.max(1, analytics.popular_companies[0].count)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <h2 className="mb-4 mt-8 flex items-center gap-2 font-bold">
            <Briefcase className="h-5 w-5 text-accent" /> Jobs by source
          </h2>
          <div className="space-y-2">
            {analytics?.jobs_by_source.map((s) => (
              <div key={s.source} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                <span className="capitalize">{s.source}</span>
                <span className="text-muted-foreground">{s.count}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <div className="space-y-8">
          <GlassCard className="p-6">
            <h2 className="mb-4 flex items-center gap-2 font-bold">
              <Users className="h-5 w-5 text-success" /> User management
            </h2>
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {usersList.map((u) => (
                <div key={u.id} className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{u.name || "User"}</p>
                    <p className="truncate text-xs text-muted-foreground">{u.email}</p>
                  </div>
                  <button
                    onClick={() => toggleRole(u)}
                    className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                      u.role === "admin"
                        ? "bg-primary/15 text-primary"
                        : "bg-white/5 text-muted-foreground hover:text-white"
                    }`}
                  >
                    {u.role}
                  </button>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <h2 className="mb-4 flex items-center gap-2 font-bold">
              <Megaphone className="h-5 w-5 text-warning" /> Broadcast notification
            </h2>
            <div className="space-y-3">
              <Input
                value={broadcastTitle}
                onChange={(e) => setBroadcastTitle(e.target.value)}
                placeholder="Notification title"
              />
              <Input
                value={broadcastBody}
                onChange={(e) => setBroadcastBody(e.target.value)}
                placeholder="Notification body (optional)"
              />
              <Button onClick={broadcast} disabled={!broadcastTitle.trim()}>
                Send to all users
              </Button>
              {broadcastResult && <p className="text-sm text-success">{broadcastResult}</p>}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

export default function AdminPage() {
  return (
    <RequireAuth>
      <AdminPanel />
    </RequireAuth>
  );
}