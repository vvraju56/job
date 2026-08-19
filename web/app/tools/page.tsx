import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  FileText,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Wand2,
} from "lucide-react";

import { GlassCard } from "@/components/ui/badge";

export const metadata: Metadata = {
  title: "Resume Tools",
  description:
    "Free AI resume tools: ATS resume score, resume optimization, cover letter generator, skill gap analysis and interview preparation.",
};

const TOOLS = [
  {
    title: "Resume Score & ATS Check",
    description:
      "Paste your resume and get an ATS score out of 99, missing keywords and actionable suggestions to pass applicant tracking systems.",
    icon: FileText,
    href: "/tools/resume-score",
    cta: "Score my resume",
  },
  {
    title: "Cover Letter Generator",
    description:
      "Generate a personalized, professional cover letter tailored to any job title and company in seconds.",
    icon: Wand2,
    href: "/tools/cover-letter",
    cta: "Generate cover letter",
  },
  {
    title: "Skill Gap Analysis",
    description:
      "Compare your skills against a target role and discover exactly what to learn next to become a top candidate.",
    icon: Sparkles,
    href: "/tools/skill-gap",
    cta: "Analyze skill gap",
  },
  {
    title: "Interview Preparation",
    description:
      "Generate likely interview questions for a specific role, job description and your own background.",
    icon: MessagesSquare,
    href: "/tools/interview",
    cta: "Prepare for interview",
  },
];

const EXTERNAL_TOOLS = [
  {
    title: "Free ATS Resume Checker",
    description:
      "Upload your resume as a PDF and get an instant ATS compatibility score from 0 to 100 with a category breakdown, keyword matching and formatting checks. Free, no login, 100% private.",
    icon: ShieldCheck,
    href: "https://free-ats-resume-checker.vercel.app/",
    cta: "Check my resume",
  },
];

export default function ToolsPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="bg-hero-glow pointer-events-none absolute inset-0" />
      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="mb-12 text-center">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-accent">
            AI Resume Tools
          </p>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-5xl">
            Land more interviews with{" "}
            <span className="text-brand-gradient">AI</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            Free, AI-powered tools that score your resume, generate cover letters,
            reveal skill gaps and prepare you for interviews.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {TOOLS.map((tool) => (
            <Link key={tool.href} href={tool.href} className="group">
              <GlassCard className="card-hover h-full p-8">
                <span className="btn-brand-gradient mb-5 flex h-14 w-14 items-center justify-center rounded-2xl shadow-glow">
                  <tool.icon className="h-7 w-7" />
                </span>
                <h2 className="text-xl font-bold">{tool.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {tool.description}
                </p>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-primary transition-colors group-hover:text-accent">
                  {tool.cta}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </GlassCard>
            </Link>
          ))}
        </div>

        <div className="mt-10">
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            External tools
          </p>
          <div className="grid gap-6 md:grid-cols-2">
            {EXTERNAL_TOOLS.map((tool) => (
              <a
                key={tool.href}
                href={tool.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group"
              >
                <GlassCard className="card-hover h-full border-dashed p-8">
                  <span className="btn-brand-gradient mb-5 flex h-14 w-14 items-center justify-center rounded-2xl shadow-glow">
                    <tool.icon className="h-7 w-7" />
                  </span>
                  <h2 className="text-xl font-bold">{tool.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {tool.description}
                  </p>
                  <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-primary transition-colors group-hover:text-accent">
                    {tool.cta}
                    <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
                  </span>
                </GlassCard>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}