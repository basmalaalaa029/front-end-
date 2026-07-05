import { cvAgentFetch } from "@/shared/lib/cv-agent-client";

export type RewriteSectionKind = "summary" | "experience" | "skills";

export type RewriteSectionRequest = {
  section: RewriteSectionKind;
  target_role?: string;
  summary?: string;
  job_title?: string;
  company?: string;
  bullets?: string[];
  skills?: string[];
  education?: string[];
};

export type RewriteSectionResponse = {
  section: RewriteSectionKind;
  summary?: string;
  bullets?: string[];
  skills?: string[];
  skills_by_category?: Record<string, string[]>;
};

const REWRITE_TIMEOUT_MS = 60_000;

export async function rewriteCvSection(
  payload: RewriteSectionRequest,
  signal?: AbortSignal,
): Promise<RewriteSectionResponse> {
  return cvAgentFetch<RewriteSectionResponse>("/rewrite-section", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
    timeoutMs: REWRITE_TIMEOUT_MS,
  });
}
