"use client";

import { FileText, Loader2, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";

interface ResumeUploadProps {
  onExtracted: (text: string, fileName: string) => void;
}

async function extractPdf(file: File): Promise<string> {
  const pdfjs = await import("pdfjs-dist");
  pdfjs.GlobalWorkerOptions.workerSrc =
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.6.205/build/pdf.worker.min.mjs";
  const data = await file.arrayBuffer();
  const doc = await pdfjs.getDocument({ data }).promise;
  const chunks: string[] = [];
  for (let page = 1; page <= doc.numPages; page++) {
    const pageData = await doc.getPage(page);
    const content = await pageData.getTextContent();
    const text = content.items
      .map((item) => ("str" in item ? (item as { str: string }).str : ""))
      .join(" ");
    chunks.push(text);
  }
  return chunks.join("\n\n");
}

async function extractDocx(file: File): Promise<string> {
  const mammoth = await import("mammoth");
  const data = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer: data });
  return result.value ?? "";
}

export function ResumeUpload({ onExtracted }: ResumeUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const handleFile = async (file: File | undefined | null) => {
    if (!file) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    setBusy(true);
    setFileError(null);
    try {
      let text = "";
      if (ext === "pdf") {
        text = await extractPdf(file);
      } else if (ext === "docx") {
        text = await extractDocx(file);
      } else if (ext === "doc") {
        text = await extractDocx(file);
      } else if (ext === "txt" || ext === "md") {
        text = await file.text();
      } else {
        setFileError("Please upload a PDF, DOCX, or TXT file.");
        setBusy(false);
        return;
      }
      if (!text.trim()) {
        setFileError("Could not extract text from that file — try a different one.");
        setBusy(false);
        return;
      }
      setFileName(file.name);
      onExtracted(text, file.name);
    } catch {
      setFileError("Failed to read that file — try converting it to PDF or DOCX.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mb-4">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.md,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = "";
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="flex w-full flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-primary/30 bg-primary/5 px-4 py-6 text-center transition hover:border-primary/60 hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? (
          <>
            <Loader2 className="h-7 w-7 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Extracting text…</span>
          </>
        ) : (
          <>
            <UploadCloud className="h-7 w-7 text-primary" />
            <span className="text-sm font-semibold">
              Upload resume (PDF, DOCX or TXT)
            </span>
            <span className="text-xs text-muted-foreground">
              Parsed locally in your browser — nothing is uploaded.
            </span>
          </>
        )}
      </button>

      {fileName && !busy && (
        <div className="mt-2 flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs">
          <FileText className="h-4 w-4 shrink-0 text-accent" />
          <span className="min-w-0 flex-1 truncate text-muted-foreground">{fileName}</span>
          <button
            type="button"
            onClick={() => setFileName(null)}
            aria-label="Clear uploaded resume"
            className="text-muted-foreground hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {fileError && <p className="mt-2 text-xs text-warning">{fileError}</p>}
    </div>
  );
}
