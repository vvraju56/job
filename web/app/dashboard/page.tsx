"use client";

import { Bell, Bookmark, Briefcase, Settings, User as UserIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { GlassCard } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { notificationsService, usersService } from "@/lib/services";
import type { Alert, Application, Job } from "@/lib/types";

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const [saved, setSaved] = useState<Job[] | null>(null);
  const [apps, setApps] = useState<Application[] | null>(null);
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    usersService.savedJobs().then(setSaved).catch(() => setSaved([]));
    usersService.applications().then(setApps).catch(() => setApps([]));
    notificationsService.alerts().then(setAlerts).catch(() => setAlerts([]));
    notificationsService
      .list(true, 200)
      .then((n) => setUnread(n.length))
      .catch(() => setUnread(0));
  }, []);

  const cards = [
    {
      label: "Saved Jobs",
      value: saved?.length ?? null,
      icon: Bookmark,
      href: "/dashboard/saved",
      color: "text-primary",
    },
    {
      label: "Applications",
      value: apps?.length ?? null,
      icon: Briefcase,
      href: "/dashboard/applications",
      color: "text-success",
    },
    {
      label: "Active Alerts",
      value: alerts?.filter((a) => a.active).length ?? null,
      icon: Bell,
      href: "/dashboard/alerts",
      color: "text-warning",
    },
    {
      label: "Unread Notifications",
      value: unread,
      icon: Settings,
      href: "/dashboard",
      color: "text-accent",
    },
  ];

  const loading = saved === null || apps === null || alerts === null;

  return (
    <div className="space-y-8">
      <GlassCard className="p-6 sm:p-8">
        <div className="flex items-center gap-4">
          <span className="btn-brand-gradient flex h-14 w-14 items-center justify-center rounded-2xl text-xl font-bold shadow-glow">
            {user?.name?.[0]?.toUpperCase() ?? "U"}
          </span>
          <div>
            <h2 className="text-xl font-bold">{user?.name}</h2>
            <p className="text-sm text-muted-foreground">
              {user?.headline ?? user?.email}
            </p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {user?.skills?.slice(0, 4).map((s) => (
                <span key={s} className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] text-primary">
                  {s}
                </span>
              ))}
            </div>
          </div>
          <Link
            href="/dashboard/profile"
            className="ml-auto flex items-center gap-2 text-sm font-semibold text-primary hover:text-accent"
          >
            <UserIcon className="h-4 w-4" /> Edit profile
          </Link>
        </div>
      </GlassCard>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((card) => (
            <Link key={card.label} href={card.href} className="group">
              <GlassCard className="card-hover h-full p-6">
                <card.icon className={`h-6 w-6 ${card.color}`} />
                <p className="mt-4 text-3xl font-extrabold">
                  {card.value ?? "—"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">{card.label}</p>
              </GlassCard>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}