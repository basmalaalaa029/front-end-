import type { AuthUser } from "@/features/auth/types/auth.types";
import {
  createEmptyWizardStep1,
  type WizardStep1Data,
} from "@/features/cv-editor/components/cv-wizard/types";

function hasContent(data: WizardStep1Data): boolean {
  return Boolean(
    data.full_name.trim() ||
      data.target_job.trim() ||
      data.email.trim() ||
      data.phone.trim() ||
      data.location.trim() ||
      data.linkedin.trim() ||
      data.github.trim() ||
      data.education.some((e) => e.degree || e.university || e.year || e.gpa) ||
      data.experience.some(
        (e) => e.job_title || e.company || e.start_date || e.end_date || e.description,
      ) ||
      data.projects.some((p) => p.name || p.tech_used || p.description) ||
      data.certifications.some(Boolean),
  );
}

/** Merge saved profile, auth defaults, and optional navigation overrides. */
export function resolveWizardStep1InitialData(
  saved: WizardStep1Data | null | undefined,
  user: AuthUser | null,
  overrides?: WizardStep1Data,
): WizardStep1Data {
  const base = hasContent(saved ?? createEmptyWizardStep1())
    ? structuredClone(saved!)
    : createEmptyWizardStep1();

  if (user) {
    if (!base.full_name.trim()) base.full_name = user.name.trim();
    if (!base.email.trim()) base.email = user.email.trim();
  }

  if (overrides?.target_job.trim()) {
    base.target_job = overrides.target_job.trim();
  }

  return base;
}
