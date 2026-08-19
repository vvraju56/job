"use client";

import { AlertCircle, Copy, Loader2 } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/tools/require-auth";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/badge";
import { Input, Textarea } from "@/components/ui/input";
import { AiKeyInput, type AiProvider } from "@/components/tools/ai-key-input";
import { ResumeUpload } from "@/components/tools/resume-upload";
import { resumeService } from "@/lib/services";

function CoverLetterTool() {
  const [resumeText, setResumeText] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<AiProvider>("openai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [letter, setLetter] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await resumeService.coverLetter({
        resume_text: resumeText,
        job_title: jobTitle,
        company_name: companyName,
        job_description: jobDescription || undefined,
        api_key: apiKey || undefined,
        provider,
      });
      setLetter(res.cover_letter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    if (!letter) return;
    await navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <GlassCard className="p-6 sm:p-8">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-semibold">Job title</label>
            <Input
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Frontend Developer"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold">Company name</label>
            <Input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Nova Labs"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="mb-1 block text-sm font-semibold">Job description (optional)</label>
          <Textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description to tailor the letter…"
            className="min-h-[120px]"
          />
        </div>
        <div className="mt-4">
          <label className="mb-1 block text-sm font-semibold">Your resume</label>
          <ResumeUpload onExtracted={(text) => setResumeText(text)} />
          <Textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your resume so the letter reflects your real experience…"
            className="min-h-[160px]"
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
          disabled={loading || !jobTitle || !companyName || !resumeText}
          onClick={generate}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Writing…" : "Generate cover letter"}
        </Button>
      </GlassCard>

      {error && (
        <div className="glass flex items-center gap-3 rounded-2xl border-warning/30 p-4 text-warning">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {letter && (
        <GlassCard className="p-6 sm:p-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Your cover letter</h2>
            <Button variant="outline" size="sm" onClick={copy}>
              <Copy className="h-4 w-4" />
              {copied ? "Copied!" : "Copy"}
            </Button>
          </div>
          <p className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
            {letter}
          </p>
        </GlassCard>
      )}
    </div>
  );
}

export default function CoverLetterPage() {
  return (
    <RequireAuth>
      <CoverLetterTool />
    </RequireAuth>
  );
}