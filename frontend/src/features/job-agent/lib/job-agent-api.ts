import { cvAgentFetch } from "@/shared/lib/cv-agent-client";
import type {
  JobMatchRequest,
  JobMatchResponse,
  JobMatchResults,
} from "../types";

export async function matchJobs(req: JobMatchRequest): Promise<JobMatchResponse> {
  return cvAgentFetch<JobMatchResponse>("/jobs/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cv_text: req.cvText,
      target_role: req.targetRole ?? "",
      location: req.location ?? "",
    }),
    timeoutMs: 60_000,
  });
}

export async function matchJobsUpload(
  file: File,
  opts: { targetRole?: string; location?: string } = {},
): Promise<JobMatchResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_role", opts.targetRole ?? "");
  form.append("location", opts.location ?? "");
  return cvAgentFetch<JobMatchResponse>("/jobs/match/upload", {
    method: "POST",
    body: form,
    timeoutMs: 120_000,
  });
}

export async function getJobResults(sessionId: string): Promise<JobMatchResults> {
  return cvAgentFetch<JobMatchResults>(
    `/jobs/results/${encodeURIComponent(sessionId)}`,
    { method: "GET" },
  );
}
