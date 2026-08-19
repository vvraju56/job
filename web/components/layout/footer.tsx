import { Briefcase, Github, Globe, Heart, Linkedin } from "lucide-react";
import Link from "next/link";

const COLUMNS = [
  {
    title: "Job Seekers",
    links: [
      { label: "Browse Jobs", href: "/jobs" },
      { label: "Companies", href: "/companies" },
      { label: "Salary Guide", href: "/jobs?sort=salary_desc" },
      { label: "Resume Tools", href: "/tools" },
    ],
  },
  {
    title: "Employers",
    links: [
      { label: "Post Jobs", href: "/jobs" },
      { label: "Pricing", href: "/jobs" },
      { label: "For Recruiters", href: "/companies" },
    ],
  },
  {
    title: "Developers",
    links: [
      { label: "API Dashboard", href: "/developers" },
      { label: "API Reference", href: "http://localhost:8000/docs" },
      { label: "Status", href: "/developers" },
    ],
  },
];

const SOCIALS = [
  { label: "Website", href: "https://makeable.example", icon: Globe },
  { label: "GitHub", href: "https://github.com", icon: Github },
  { label: "LinkedIn", href: "https://linkedin.com", icon: Linkedin },
];

export function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-white/10 bg-surface/60">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="grid gap-12 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5">
              <span className="btn-brand-gradient flex h-10 w-10 items-center justify-center rounded-xl shadow-glow">
                <Briefcase className="h-5 w-5" />
              </span>
              <span className="text-xl font-bold">
                Makeable<span className="text-brand-gradient"> Jobs</span>
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">
              One Search. Every Opportunity. Aggregate job listings from the
              world&apos;s leading job portals and apply on the original
              website.
            </p>
            <div className="mt-6 flex gap-3">
              {SOCIALS.map(({ label, href, icon: Icon }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="glass-pill flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/40 hover:text-primary hover:shadow-glow"
                >
                  <Icon className="h-5 w-5" />
                </a>
              ))}
            </div>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
                {col.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-primary"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © 2026 Makeable Jobs. All rights reserved.
          </p>
          <p className="text-sm text-muted-foreground">
            Made with{" "}
            <Heart className="inline h-4 w-4 fill-primary text-primary" /> by{" "}
            <span className="font-semibold text-accent">VV</span>
          </p>
        </div>
      </div>
    </footer>
  );
}