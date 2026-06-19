import { cvAgentFetch } from "@/shared/lib/cv-agent-client";
import type { GenerateAiCvResponse, WizardStep1Data } from "../components/cv-wizard/types";

const GENERATE_TIMEOUT_MS = 3 * 60 * 1000;

export async function generateAiCv(
  data: WizardStep1Data,
  signal?: AbortSignal,
): Promise<GenerateAiCvResponse> {
  return cvAgentFetch<GenerateAiCvResponse>("/generate-ai-cv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    signal,
    timeoutMs: GENERATE_TIMEOUT_MS,
  });
}
