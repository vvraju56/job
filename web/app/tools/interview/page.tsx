"use client";

import { AlertCircle, Loader2 } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/tools/require-auth";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/badge";
import { Input, Textarea } from "@/components/ui/input";
import { AiKeyInput, type AiProvider } from "@/components/tools/ai-key-input";
import { ResumeUpload } from "@/components/tools/resume-upload";
import { resumeService } from "@/lib/services";

function InterviewTool() {
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<AiProvider>("openai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<string[] | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await resumeService.interviewPrep({
        job_title: jobTitle,
        job_description: jobDescription || undefined,
        resume_text: resumeText || undefined,
        api_key: apiKey || undefined,
        provider,
      });
      setQuestions(res.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <GlassCard className="p-6 sm:p-8">
        <div className="mb-4">
          <label className="mb-1 block text-sm font-semibold">Job title</label>
          <Input
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Senior Flutter Developer"
          />
        </div>
        <div className="mb-4">
          <label className="mb-1 block text-sm font-semibold">Job description (optional)</label>
          <Textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description for tailored questions…"
            className="min-h-[120px]"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold">Your resume (optional)</label>
          <ResumeUpload onExtracted={(text) => setResumeText(text)} />
          <Textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your resume to get questions about your specific experience…"
            className="min-h-[120px]"
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
          disabled={loading || !jobTitle}
          onClick={generate}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Preparing…" : "Generate interview questions"}
        </Button>
      </GlassCard>

      {error && (
        <div className="glass flex items-center gap-3 rounded-2xl border-warning/30 p-4 text-warning">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {questions && questions.length > 0 && (
        <GlassCard className="p-6 sm:p-8">
          <h2 className="mb-4 font-semibold">
            Likely interview questions for {jobTitle}
          </h2>
          <ol className="space-y-3">
            {questions.map((q, i) => (
              <li key={q} className="flex gap-3 text-sm text-muted-foreground">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
                  {i + 1}
                </span>
                {q}
              </li>
            ))}
          </ol>
        </GlassCard>
      )}
    </div>
  );
}

export default function InterviewPrepPage() {
  return (
    <RequireAuth>
      <InterviewTool />
    </RequireAuth>
  );
}