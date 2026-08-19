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
import type { SkillGap } from "@/lib/types";

function SkillGapTool() {
  const [resumeText, setResumeText] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<AiProvider>("openai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SkillGap | null>(null);

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await resumeService.skillGap({
        resume_text: resumeText,
        target_role: targetRole,
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
        <div className="mb-4">
          <label className="mb-1 block text-sm font-semibold">Target role</label>
          <Input
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Flutter Developer"
          />
        </div>
        <label className="mb-1 block text-sm font-semibold">Your resume</label>
        <ResumeUpload onExtracted={(text) => setResumeText(text)} />
        <Textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder="Paste your resume so we can map your current skills…"
          className="min-h-[220px]"
        />
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
          disabled={loading || !targetRole || resumeText.length < 30}
          onClick={analyze}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Analyzing…" : "Analyze skill gap"}
        </Button>
      </GlassCard>

      {error && (
        <div className="glass flex items-center gap-3 rounded-2xl border-warning/30 p-4 text-warning">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {result && (
        <>
          <GlassCard className="p-6 sm:p-8">
            <h3 className="mb-3 font-semibold text-success">Your current skills</h3>
            {result.current_skills.length ? (
              <div className="flex flex-wrap gap-2">
                {result.current_skills.map((s) => (
                  <span key={s} className="rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs text-success">
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No recognized skills found.</p>
            )}
          </GlassCard>

          <GlassCard className="p-6 sm:p-8">
            <h3 className="mb-3 font-semibold text-warning">
              Skills to add for {targetRole}
            </h3>
            {result.missing_skills.length ? (
              <div className="flex flex-wrap gap-2">
                {result.missing_skills.map((s) => (
                  <span key={s} className="rounded-full border border-warning/30 bg-warning/10 px-3 py-1 text-xs text-warning">
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-success">You already cover the key skills. Nice work!</p>
            )}
          </GlassCard>

          {result.recommended_learning.length > 0 && (
            <GlassCard className="p-6 sm:p-8">
              <h3 className="mb-3 font-semibold text-accent">Recommended learning</h3>
              <ul className="space-y-2">
                {result.recommended_learning.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                    <span className="text-accent">→</span> {item}
                  </li>
                ))}
              </ul>
            </GlassCard>
          )}
        </>
      )}
    </div>
  );
}

export default function SkillGapPage() {
  return (
    <RequireAuth>
      <SkillGapTool />
    </RequireAuth>
  );
}