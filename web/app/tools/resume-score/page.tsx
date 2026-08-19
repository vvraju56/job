"use client";

import { AlertCircle, ArrowUpRight, Loader2 } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/tools/require-auth";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/badge";
import { Textarea, Input } from "@/components/ui/input";
import { AiKeyInput, type AiProvider } from "@/components/tools/ai-key-input";
import { ResumeUpload } from "@/components/tools/resume-upload";
import { resumeService } from "@/lib/services";
import type { ResumeAnalysis } from "@/lib/types";

const SAMPLE_RESUME = `Soumya Iyer
Senior Software Engineer

Summary
Full-stack engineer with 6 years of experience building production web applications with React, TypeScript and Python. Passionate about clean architecture and developer experience.

Experience
Senior Software Engineer, FinEdge (2022 - Present)
- Built a real-time analytics dashboard used by 40,000+ daily users, improving load time by 35%
- Led migration from a legacy REST monolith to modular services with FastAPI and PostgreSQL
- Introduced CI/CD pipelines with Docker and GitHub Actions, cutting release time in half
- Mentored 4 junior engineers and drove adoption of code review best practices

Software Engineer, Nova Labs (2019 - 2022)
- Shipped customer-facing features with Next.js, React and Tailwind CSS
- Designed and optimized SQL queries, reducing database costs by 20%
- Collaborated with designers to ship a design system used across 5 products

Skills
TypeScript, React, Next.js, Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS, Git, CI/CD, REST, GraphQL`;

function ScoreRing({ score }: { score: number }) {
  const color = score >= 75 ? "#22C55E" : score >= 50 ? "#F59E0B" : "#EF4444";
  return (
    <div className="flex items-center gap-6">
      <div
        className="flex h-32 w-32 items-center justify-center rounded-full"
        style={{
          background: `conic-gradient(${color} ${score * 3.6}deg, rgba(148,163,184,0.15) 0deg)`,
        }}
      >
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-surface">
          <span className="text-3xl font-extrabold" style={{ color }}>
            {score}
          </span>
        </div>
      </div>
      <div>
        <p className="text-sm text-muted-foreground">ATS score</p>
        <p className="text-2xl font-bold">out of 99</p>
      </div>
    </div>
  );
}

function ResumeScoreTool() {
  const [resumeText, setResumeText] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<AiProvider>("openai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResumeAnalysis | null>(null);

  const run = async (text: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await resumeService.analyze({
        resume_text: text,
        target_role: targetRole || undefined,
        api_key: apiKey || undefined,
        provider,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <GlassCard className="p-6 sm:p-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold">Paste your resume</label>
            <button
              onClick={() => setResumeText(SAMPLE_RESUME)}
              className="text-xs text-primary hover:text-accent"
            >
              Use sample resume
            </button>
          </div>
          <a
            href="https://free-ats-resume-checker.vercel.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:text-accent"
          >
            Try the free PDF ATS checker
            <ArrowUpRight className="h-3 w-3" />
          </a>
        </div>
        <ResumeUpload onExtracted={(text) => setResumeText(text)} />
        <Textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder="Paste your full resume text here (minimum 50 characters)…"
          className="min-h-[260px] font-mono text-xs"
        />
        <div className="mt-4">
          <label className="mb-1 block text-sm font-semibold">Target role (optional)</label>
          <Input
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Flutter Developer"
          />
        </div>
        <div className="mt-4">
          <AiKeyInput
            apiKey={apiKey}
            setApiKey={setApiKey}
            provider={provider}
            setProvider={setProvider}
          />
        </div>
        <Button
          className="mt-5 w-full sm:w-auto"
          disabled={loading || resumeText.length < 50}
          onClick={() => run(resumeText)}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Analyzing…" : "Analyze resume"}
        </Button>
      </GlassCard>

      {error && (
        <div className="glass flex items-center gap-3 rounded-2xl border-warning/30 p-4 text-warning">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {result && (
        <GlassCard className="p-6 sm:p-8">
          <ScoreRing score={result.ats_score} />
          <p className="mt-4 text-sm text-muted-foreground">{result.summary}</p>

          {result.missing_keywords.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-2 font-semibold text-warning">Missing keywords</h3>
              <div className="flex flex-wrap gap-2">
                {result.missing_keywords.map((kw) => (
                  <span key={kw} className="rounded-full border border-warning/30 bg-warning/10 px-3 py-1 text-xs text-warning">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.suggestions.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-2 font-semibold text-success">Suggestions</h3>
              <ul className="space-y-2">
                {result.suggestions.map((s) => (
                  <li key={s} className="flex gap-2 text-sm text-muted-foreground">
                    <span className="text-success">•</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </GlassCard>
      )}
    </div>
  );
}

export default function ResumeScorePage() {
  return (
    <RequireAuth>
      <ResumeScoreTool />
    </RequireAuth>
  );
}