"use client";

import { ExternalLink, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { usersService } from "@/lib/services";
import type { Job } from "@/lib/types";

export function ApplyButton({ job }: { job: Job }) {
  const { user } = useAuth();
  const router = useRouter();
  const [tracking, setTracking] = useState(false);

  const handleApply = async () => {
    if (!user) {
      router.push(`/login?next=/jobs/${job.id}`);
      return;
    }
    setTracking(true);
    try {
      await usersService.createApplication({
        job_id: job.id,
        company_name: job.company_name,
        role: job.title,
        applied_url: job.apply_url,
        status: "applied",
      });
    } catch {
      /* tracking is best-effort; still open the portal */
    } finally {
      setTracking(false);
      window.open(job.apply_url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <Button size="lg" onClick={handleApply} disabled={tracking} className="w-full sm:w-auto">
      {tracking ? (
        <Loader2 className="h-5 w-5 animate-spin" />
      ) : (
        <ExternalLink className="h-5 w-5" />
      )}
      Apply on {job.apply_on === "Original Website" ? "Original Website" : job.apply_on}
    </Button>
  );
}