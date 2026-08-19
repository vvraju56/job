"use client";

import { Filter, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { DatePosted, JobType, Level, SearchFilters, JobSource } from "@/lib/types";
import {
  JOB_TYPE_LABELS,
  LEVEL_LABELS,
  SOURCE_LABELS,
} from "@/lib/types";

export function JobFilters({
  filters,
  onApply,
  className,
}: {
  filters: SearchFilters;
  onApply: (filters: SearchFilters) => void;
  className?: string;
}) {
  const [draft, setDraft] = useState<SearchFilters>(filters);

  const set = (patch: Partial<SearchFilters>) =>
    setDraft((prev) => ({ ...prev, ...patch }));

  const apply = () => onApply({ ...draft, page: 1 });

  const clear = () => {
    const empty: SearchFilters = { q: filters.q, sort: "recent", page: 1 };
    setDraft(empty);
    onApply(empty);
  };

  const hasActive =
    draft.remote ||
    draft.salary_min != null ||
    draft.salary_max != null ||
    draft.job_type ||
    draft.level ||
    draft.experience_min != null ||
    draft.experience_max != null ||
    draft.source ||
    draft.location ||
    draft.date_posted;

  return (
    <div className={cn("space-y-6", className)}>
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          <SlidersHorizontal className="h-4 w-4" /> Filters
        </h3>
        {hasActive && (
          <button
            onClick={clear}
            className="flex items-center gap-1 text-xs text-primary hover:text-accent"
          >
            <X className="h-3.5 w-3.5" /> Clear all
          </button>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Location</label>
        <Input
          value={draft.location ?? ""}
          onChange={(e) => set({ location: e.target.value || undefined })}
          placeholder="City, state, or Remote"
        />
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Salary range</label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="number"
            value={draft.salary_min ?? ""}
            onChange={(e) =>
              set({ salary_min: e.target.value ? Number(e.target.value) : undefined })
            }
            placeholder="Min ₹"
          />
          <Input
            type="number"
            value={draft.salary_max ?? ""}
            onChange={(e) =>
              set({ salary_max: e.target.value ? Number(e.target.value) : undefined })
            }
            placeholder="Max ₹"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Job type</label>
        <Select
          value={draft.job_type ?? ""}
          onChange={(e) => set({ job_type: (e.target.value || undefined) as JobType | undefined })}
        >
          <option value="">All types</option>
          {(Object.keys(JOB_TYPE_LABELS) as JobType[]).map((t) => (
            <option key={t} value={t}>
              {JOB_TYPE_LABELS[t]}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Experience level</label>
        <Select
          value={draft.level ?? ""}
          onChange={(e) => set({ level: (e.target.value || undefined) as Level | undefined })}
        >
          <option value="">All levels</option>
          {(Object.keys(LEVEL_LABELS) as Level[]).map((l) => (
            <option key={l} value={l}>
              {LEVEL_LABELS[l]}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Experience (years)</label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="number"
            value={draft.experience_min ?? ""}
            onChange={(e) =>
              set({ experience_min: e.target.value ? Number(e.target.value) : undefined })
            }
            placeholder="Min"
          />
          <Input
            type="number"
            value={draft.experience_max ?? ""}
            onChange={(e) =>
              set({ experience_max: e.target.value ? Number(e.target.value) : undefined })
            }
            placeholder="Max"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Posted within</label>
        <Select
          value={draft.date_posted ?? ""}
          onChange={(e) =>
            set({ date_posted: (e.target.value || undefined) as DatePosted | undefined })
          }
        >
          <option value="">Anytime</option>
          <option value="today">Today</option>
          <option value="3days">Last 3 days</option>
          <option value="week">This week</option>
          <option value="month">This month</option>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground">Source</label>
        <Select
          value={draft.source ?? ""}
          onChange={(e) => set({ source: (e.target.value || undefined) as JobSource | undefined })}
        >
          <option value="">All sources</option>
          {(Object.keys(SOURCE_LABELS) as JobSource[]).map((s) => (
            <option key={s} value={s}>
              {SOURCE_LABELS[s]}
            </option>
          ))}
        </Select>
      </div>

      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
        <input
          type="checkbox"
          checked={draft.remote ?? false}
          onChange={(e) => set({ remote: e.target.checked })}
          className="h-4 w-4 accent-primary"
        />
        <span className="text-sm font-medium text-white">
          Remote only
          <span className="ml-1 text-xs text-muted-foreground">work from anywhere</span>
        </span>
      </label>

      <Button className="w-full" onClick={apply}>
        <Filter className="h-4 w-4" /> Apply filters
      </Button>
    </div>
  );
}