"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, type ReactNode } from "react";

import { Spinner } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";

function RequireAuthInner({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    if (!loading && !user) {
      const next = params.get("next");
      router.replace(`/login${next ? `?next=${encodeURIComponent(next)}` : ""}`);
    }
  }, [loading, user, router, params]);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!user) return null;
  return <>{children}</>;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  return (
    <Suspense>
      <RequireAuthInner>{children}</RequireAuthInner>
    </Suspense>
  );
}