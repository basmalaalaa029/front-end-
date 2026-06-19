import { useCvDraftStore } from "@/features/cv-editor/stores/cv-draft-store";
import { cvDataToMarkdown } from "@/features/cv-editor/lib/cv-to-profile";

export type DraftAnalysisInputs = {
  cvText: string;
  jobDescription: string;
  targetRole: string;
  company: string;
};

/** Build analyzer request fields from the persisted CV editor draft. */
export function getDraftAnalysisInputs(): DraftAnalysisInputs | null {
  const { data, jobDescription } = useCvDraftStore.getState();
  const cvText = cvDataToMarkdown(data).trim();
  if (cvText.length < 50) return null;

  const targetRole =
    data.role.trim() ||
    data.education.map((e) => e.degree.trim()).find(Boolean) ||
    data.name.trim() ||
    "Target role";

  return {
    cvText,
    jobDescription: jobDescription.trim(),
    targetRole,
    company: "",
  };
}

function safeFileStem(name: string): string {
  const stem = name.replace(/[^\w.-]+/g, "_").replace(/^_+|_+$/g, "");
  return stem.slice(0, 48) || "CV";
}

/** CV editor draft as a `.txt` file for POST /analyze/upload. */
export function getDraftAnalysisFile(): { file: File; inputs: Omit<DraftAnalysisInputs, "cvText"> } | null {
  const draft = getDraftAnalysisInputs();
  if (!draft) return null;

  const stem = safeFileStem(draft.targetRole || "CV");
  const file = new File([draft.cvText], `${stem}.txt`, { type: "text/plain" });

  return {
    file,
    inputs: {
      jobDescription: draft.jobDescription,
      targetRole: draft.targetRole,
      company: draft.company,
    },
  };
}

/** Context fields auto-filled from the editor draft (role + stored job description). */
export function getDraftAnalysisContext(): Omit<DraftAnalysisInputs, "cvText"> | null {
  const draft = getDraftAnalysisInputs();
  if (!draft) return null;
  return {
    jobDescription: draft.jobDescription,
    targetRole: draft.targetRole,
    company: draft.company,
  };
}

export function cvTextToAnalysisFile(cvText: string, label = "CV"): File {
  const stem = safeFileStem(label);
  return new File([cvText], `${stem}.txt`, { type: "text/plain" });
}

export function formatCvFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
