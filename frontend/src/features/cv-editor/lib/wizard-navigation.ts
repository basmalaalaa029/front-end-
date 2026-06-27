import type { TemplateId } from "@/features/cv-editor/data/cv-templates";

/** Default template when opening the AI wizard from analysis. */
export const DEFAULT_WIZARD_TEMPLATE: TemplateId = "modern";

export type CvWizardNavigationState = {
  fromAnalysis?: boolean;
  targetRole?: string;
};

export function parseWizardNavigationState(
  state: unknown,
): CvWizardNavigationState | null {
  if (!state || typeof state !== "object") return null;
  const s = state as CvWizardNavigationState;
  if (!s.fromAnalysis && !s.targetRole?.trim()) return null;
  return s;
}
