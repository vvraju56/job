"use client";

import { KeyRound } from "lucide-react";
import { useState } from "react";

import { Input, Select } from "@/components/ui/input";

export type AiProvider = "openai" | "gemini";

export function AiKeyInput({
  apiKey,
  setApiKey,
  provider,
  setProvider,
}: {
  apiKey: string;
  setApiKey: (v: string) => void;
  provider: AiProvider;
  setProvider: (p: AiProvider) => void;
}) {
  const [show, setShow] = useState(false);

  return (
    <div className="rounded-2xl border border-white/12 bg-white/[0.02] p-4">
      <p className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
        <KeyRound className="h-3.5 w-3.5 text-primary" />
        Optional — bring your own AI key for a smarter result. Leave empty to use the built-in engine.
      </p>
      <div className="grid gap-3 sm:grid-cols-[1fr_140px]">
        <div className="relative">
          <Input
            type={show ? "text" : "password"}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={provider === "openai" ? "sk-… (OpenAI)" : "AIza… (Gemini)"}
            className="pr-20"
            autoComplete="off"
          />
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-primary"
          >
            {show ? "Hide" : "Show"}
          </button>
        </div>
        <Select
          value={provider}
          onChange={(e) => {
            setProvider(e.target.value as AiProvider);
            setApiKey("");
          }}
        >
          <option value="openai">OpenAI</option>
          <option value="gemini">Gemini</option>
        </Select>
      </div>
      <p className="mt-2 text-[11px] text-muted-foreground/70">
        Your key is sent only to {provider === "openai" ? "OpenAI" : "Google Gemini"} and is never stored.
      </p>
    </div>
  );
}
