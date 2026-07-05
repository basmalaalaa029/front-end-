import type { CvData } from "@/features/cv-editor/data/cv-types";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";
import { cvDataToMarkdown } from "@/features/cv-editor/lib/cv-to-profile";
import { useCvDraftStore } from "@/features/cv-editor/stores/cv-draft-store";

/** True when the persisted editor draft has enough content to resume editing. */
export function hasMeaningfulCvDraft(data: CvData): boolean {
  return cvDataToMarkdown(data).trim().length >= 50;
}

/** Best path for returning to CV editing (editor if a draft exists, otherwise template gallery). */
export function getCvEditorResumePath(
  lastTemplateId: TemplateId | null,
  data: CvData,
): string {
  if (lastTemplateId && hasMeaningfulCvDraft(data)) {
    return `/dashboard/editor/build/${lastTemplateId}`;
  }
  return "/dashboard/editor";
}

export function useCvCreatorPath(): string {
  const lastTemplateId = useCvDraftStore((s) => s.lastTemplateId);
  const data = useCvDraftStore((s) => s.data);
  return getCvEditorResumePath(lastTemplateId, data);
}

export function isCvCreatorRoute(pathname: string): boolean {
  return pathname === "/dashboard/editor" || pathname.startsWith("/dashboard/editor/");
}
