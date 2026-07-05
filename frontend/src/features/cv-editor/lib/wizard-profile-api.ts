import api from "@/lib/api";
import type { WizardStep1Data } from "@/features/cv-editor/components/cv-wizard/types";

export async function fetchWizardProfile(): Promise<WizardStep1Data | null> {
  const res = await api.get<{ profile: WizardStep1Data | null }>("/users/wizard-profile");
  return res.data?.profile ?? null;
}

export async function saveWizardProfile(profile: WizardStep1Data): Promise<void> {
  await api.put("/users/wizard-profile", profile);
}
