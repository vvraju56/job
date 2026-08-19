import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "Resume Tools",
  description:
    "Free AI resume tools: ATS resume score, cover letter generator, skill gap analysis and interview preparation.",
};

export default function ToolsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative overflow-hidden">
      <div className="bg-hero-glow pointer-events-none absolute inset-0" />
      <div className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <nav className="mb-6 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-primary">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/tools" className="hover:text-primary">Resume Tools</Link>
        </nav>
        {children}
      </div>
    </div>
  );
}