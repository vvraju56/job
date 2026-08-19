"use client";

import { Bookmark, BookmarkCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth-context";
import { useSavedJobs } from "@/lib/hooks/use-saved-jobs";
import { cn } from "@/lib/utils";
import type { Job } from "@/lib/types";

export function SaveButton({ job, className }: { job: Job; className?: string }) {
  const { user } = useAuth();
  const { isSaved, toggleSave } = useSavedJobs();
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const saved = isSaved(job.id);

  const onClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      router.push("/login?next=/jobs");
      return;
    }
    setPending(true);
    try {
      await toggleSave(job);
    } finally {
      setPending(false);
    }
  };

  return (
    <button
      onClick={onClick}
      aria-label={saved ? "Remove from saved jobs" : "Save job"}
      aria-pressed={saved}
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-muted-foreground transition-all duration-200 hover:border-primary/40 hover:text-primary",
        saved && "border-primary/40 bg-primary/15 text-primary shadow-glow",
        pending && "opacity-60",
        className,
      )}
    >
      {saved ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
    </button>
  );
}