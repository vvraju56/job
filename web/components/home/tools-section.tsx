"use client";

import { motion } from "framer-motion";
import { ArrowRight, FileText, Sparkles, Wand2 } from "lucide-react";
import Link from "next/link";

const TOOLS = [
  {
    title: "Resume Score",
    description: "Get an instant ATS score for your resume with actionable fixes.",
    icon: FileText,
    href: "/tools/resume-score",
  },
  {
    title: "Cover Letter Generator",
    description: "Create personalized cover letters for any role in seconds.",
    icon: Wand2,
    href: "/tools/cover-letter",
  },
  {
    title: "Skill Gap Analysis",
    description: "Discover what skills you need to land your target role.",
    icon: Sparkles,
    href: "/tools/skill-gap",
  },
];

export function ToolsSection() {
  return (
    <section className="relative overflow-hidden py-16">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6">
        <div className="mb-8 text-center">
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-accent">
            AI Resume Tools
          </p>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Land More Interviews with AI
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
            Free, AI-powered tools that help you optimize your resume and prepare
            for interviews.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {TOOLS.map((tool, i) => (
            <motion.div
              key={tool.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
            >
              <Link
                href={tool.href}
                className="group glass card-hover flex h-full flex-col rounded-2xl p-6"
              >
                <span className="btn-brand-gradient mb-4 flex h-12 w-12 items-center justify-center rounded-2xl shadow-glow">
                  <tool.icon className="h-6 w-6" />
                </span>
                <h3 className="text-lg font-semibold">{tool.title}</h3>
                <p className="mt-2 flex-1 text-sm text-muted-foreground">
                  {tool.description}
                </p>
                <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-primary transition-colors group-hover:text-accent">
                  Try it free
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}