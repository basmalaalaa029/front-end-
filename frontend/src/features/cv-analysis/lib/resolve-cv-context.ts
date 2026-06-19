import { useCvDraftStore } from "@/features/cv-editor/stores/cv-draft-store";
import type { AnalysisFileSource } from "@/features/cv-analysis/lib/cv-analysis-api";
import {
  extractCvContextFromText,
  readCvFileAsText,
  type ExtractedCvContext,
} from "@/features/cv-analysis/lib/extract-cv-context";

export type ResolvedAnalysisContext = {
  targetRole: string;
  company: string;
  jobDescription: string;
};

function mergeWithEditorJobDescription(ctx: ExtractedCvContext): ResolvedAnalysisContext {
  const storeJd = useCvDraftStore.getState().jobDescription.trim();
  return {
    targetRole: ctx.targetRole,
    company: ctx.company,
    jobDescription: storeJd || ctx.jobDescription,
  };
}

/** Resolve role / company / profile context from a CV file (upload or editor export). */
export async function resolveAnalysisContextFromFile(
  file: File,
  source: AnalysisFileSource,
): Promise<ResolvedAnalysisContext> {
  const empty: ResolvedAnalysisContext = {
    targetRole: "Target role",
    company: "",
    jobDescription: "",
  };

  try {
    const text = await readCvFileAsText(file);
    const fromText = text.length >= 50 ? extractCvContextFromText(text) : null;

    if (source === "editor") {
      const raw = fromText ? text : await file.text();
      return mergeWithEditorJobDescription(extractCvContextFromText(raw));
    }

    if (fromText && hasDetectedCvContext(fromText)) {
      return fromText;
    }

    return fromText ?? empty;
  } catch {
    // PDF/DOCX parse may fail if the API is unreachable — analysis upload still works.
    return empty;
  }
}

export function hasDetectedCvContext(ctx: ResolvedAnalysisContext): boolean {
  return (
    (ctx.targetRole !== "Target role" && ctx.targetRole.length > 0) ||
    ctx.company.length > 0 ||
    ctx.jobDescription.length > 0
  );
}
