import { CvAgentClientError, cvAgentFetch } from "@/shared/lib/cv-agent-client";
import type {
  JobMatchRequest,
  JobMatchResponse,
  JobMatchResults,
  JobMatchStatus,
} from "../types";

const JOB_POLL_MS = 2000;
const JOB_MAX_POLL_MS = 5 * 60 * 1000;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

export async function getJobMatchStatus(sessionId: string): Promise<JobMatchStatus> {
  return cvAgentFetch<JobMatchStatus>(
    `/jobs/status/${encodeURIComponent(sessionId)}`,
    { method: "GET", timeoutMs: 30_000 },
  );
}

export async function getJobResults(sessionId: string): Promise<JobMatchResults> {
  return cvAgentFetch<JobMatchResults>(
    `/jobs/result/${encodeURIComponent(sessionId)}`,
    { method: "GET", timeoutMs: 30_000 },
  );
}

/** Poll status until ready, then fetch ranked jobs. */
export async function waitForJobResults(
  sessionId: string,
  onStatus?: (status: JobMatchStatus) => void,
): Promise<JobMatchResults> {
  const started = Date.now();
  while (Date.now() - started < JOB_MAX_POLL_MS) {
    const status = await getJobMatchStatus(sessionId);
    onStatus?.(status);
    if (status.status === "failed") {
      throw new CvAgentClientError(status.error ?? "Job match failed");
    }
    if (status.status === "ready") {
      return getJobResults(sessionId);
    }
    await sleep(JOB_POLL_MS);
  }
  throw new CvAgentClientError(
    "Job matching took too long (>5 min). Please try again.",
  );
}
