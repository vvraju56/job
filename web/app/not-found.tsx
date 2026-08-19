import Link from "next/link";
import { Compass } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
      <div className="bg-hero-glow pointer-events-none absolute inset-0" />
      <span className="btn-brand-gradient relative flex h-16 w-16 items-center justify-center rounded-2xl shadow-glow">
        <Compass className="h-8 w-8" />
      </span>
      <h1 className="relative mt-6 text-5xl font-extrabold">404</h1>
      <p className="relative mt-3 max-w-md text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
        Let&apos;s get you back to finding opportunities.
      </p>
      <div className="relative mt-8">
        <Link href="/">
          <Button>Back to Home</Button>
        </Link>
      </div>
    </div>
  );
}