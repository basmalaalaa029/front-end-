/**
 * Thin client for CV Agent FastAPI — generation pipeline on port 8000.
 */
import {
  CV_AGENT_BASE,
  CvAgentClientError,
  cvAgentFetch,
  cvAgentFetchRaw,
  readCvAgentError,
} from "@/shared/lib/cv-agent-client";

export type CvAgentTone = "professional" | "creative" | "technical";

export interface CvAgentExperience {
  job_title: string;
  company: string;
  location?: string;
  start_date: string;
  end_date: string;
  bullets: string[];
}

export interface CvAgentProject {
  name: string;
  tech_used?: string;
  description: string;
}

export interface CvAgentEducation {
  degree: string;
  university: string;
  year: string;
  gpa?: string;
}

export interface CvAgentGenerateRequest {
  full_name: string;
  target_role: string;
  target_industry?: string;
  years_experience?: string;
  summary?: string;
  tone?: CvAgentTone;
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
  location?: string;
  experience?: CvAgentExperience[];
  projects?: CvAgentProject[];
  education_structured?: CvAgentEducation[];
  /** @deprecated legacy flat lines */
  education?: string[];
  skills: string[];
  /** @deprecated legacy flat blocks */
  experiences?: string[];
  achievements?: string[];
  certifications?: string[];
  languages?: string[];
  job_description?: string;
  parsed_resume?: string;
  max_iterations?: number;
  score_threshold?: number;
  num_candidates?: number;
  session_id?: string;
}

export interface CvAgentGenerateResponse {
  session_id: string;
  status: string;
  message: string;
  template_cv?: string;
}

export type CvAgentSessionStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export interface CvAgentStatus {
  session_id: string;
  status: CvAgentSessionStatus;
  created_at: string;
  updated_at: string;
  progress_msgs: string[];
  error?: string | null;
}

export interface CvAgentScores {
  clarity_score: number;
  structure_score: number;
  impact_score: number;
  skills_relevance_score: number;
  ats_readiness_score: number;
  overall_score: number;
  strengths?: string[];
  weaknesses?: string[];
  improvement_suggestions?: string[];
  rewrite_suggestions?: string[];
}

export interface CvAgentResult {
  session_id: string;
  status: CvAgentSessionStatus;
  candidate_name: string;
  target_role: string;
  total_iterations: number;
  final_cv: string;
  template_cv?: string;
  enhanced_data?: Record<string, unknown> | null;
  final_scores?: CvAgentScores | null;
  score_trajectory: number[];
  jd_keywords: string[];
  node_errors: string[];
  total_latency_ms: number;
  error?: string | null;
}

class CvAgentApiError extends CvAgentClientError {
  details?: unknown;
  constructor(message: string, status?: number, details?: unknown) {
    super(message, status);
    this.name = "CvAgentApiError";
    this.details = details;
  }
}

/** Per-request fetch timeouts so a single hung TCP connection can't stall forever. */
const START_FETCH_TIMEOUT_MS = 30_000;
const POLL_FETCH_TIMEOUT_MS = 30_000;
/** Default overall cap for a generation if the caller doesn't pass one. */
const DEFAULT_GENERATION_TIMEOUT_MS = 15 * 60 * 1000;

export async function startGeneration(
  payload: CvAgentGenerateRequest,
  signal?: AbortSignal,
): Promise<CvAgentGenerateResponse> {
  try {
    return await cvAgentFetch<CvAgentGenerateResponse>("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
      timeoutMs: START_FETCH_TIMEOUT_MS,
    });
  } catch (err) {
    if (err instanceof CvAgentClientError) {
      throw new CvAgentApiError(err.message, err.status);
    }
    throw err;
  }
}

export async function getStatus(
  sessionId: string,
  signal?: AbortSignal,
): Promise<CvAgentStatus> {
  return cvAgentFetch<CvAgentStatus>(`/status/${encodeURIComponent(sessionId)}`, {
    method: "GET",
    signal,
    timeoutMs: POLL_FETCH_TIMEOUT_MS,
  });
}

export async function getResult(
  sessionId: string,
  signal?: AbortSignal,
): Promise<CvAgentResult> {
  return cvAgentFetch<CvAgentResult>(`/result/${encodeURIComponent(sessionId)}`, {
    method: "GET",
    signal,
  });
}

export interface PollOptions {
  signal?: AbortSignal;
  intervalMs?: number;
  timeoutMs?: number;
  onProgress?: (status: CvAgentStatus) => void;
}

export async function waitForCompletion(
  sessionId: string,
  opts: PollOptions = {},
): Promise<CvAgentStatus> {
  const interval = opts.intervalMs ?? 2000;
  const deadline = Date.now() + (opts.timeoutMs ?? DEFAULT_GENERATION_TIMEOUT_MS);
  while (true) {
    if (opts.signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const s = await getStatus(sessionId, opts.signal);
    opts.onProgress?.(s);
    if (s.status === "completed" || s.status === "failed") return s;
    if (Date.now() > deadline) {
      throw new CvAgentApiError("Timed out waiting for CV generation.");
    }
    await new Promise<void>((resolve, reject) => {
      const tid = setTimeout(resolve, interval);
      opts.signal?.addEventListener(
        "abort",
        () => {
          clearTimeout(tid);
          reject(new DOMException("Aborted", "AbortError"));
        },
        { once: true },
      );
    });
  }
}

export async function fetchPdfBlob(
  sessionId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const res = await cvAgentFetchRaw(
    `/result/${encodeURIComponent(sessionId)}/pdf`,
    {
      method: "GET",
      headers: { Accept: "application/pdf" },
      signal,
    },
  );
  return res.blob();
}

export function saveBlobAsFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

export async function downloadDirectPdf(
  markdown: string,
  candidateName: string,
  signal?: AbortSignal,
): Promise<void> {
  const res = await cvAgentFetchRaw("/pdf/direct", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/pdf",
    },
    body: JSON.stringify({ markdown, candidate_name: candidateName }),
  });
  const blob = await res.blob();
  const safe = (candidateName || "CV").replace(/[^A-Za-z0-9_\- ]/g, "").trim() || "CV";
  saveBlobAsFile(blob, `${safe.replace(/\s+/g, "_")}.pdf`);
}

/** i18n keys under cvEditor.gen — never expose raw pipeline debug text in the UI. */
export type GenProgressMessageKey =
  | "queued"
  | "loadingModel"
  | "writing"
  | "scoring"
  | "refining"
  | "working";

export function mapGenerationProgressMessage(
  lastMsg: string | undefined,
  sessionStatus: CvAgentSessionStatus,
): GenProgressMessageKey {
  if (lastMsg) {
    console.debug("[CV Agent] progress:", lastMsg);
  }

  if (sessionStatus === "pending") {
    return "queued";
  }

  if (!lastMsg) {
    return "working";
  }

  const lower = lastMsg.toLowerCase();

  if (
    lower.includes("scoring") ||
    lower.includes("reviewing your cv")
  ) {
    return "scoring";
  }

  if (
    lower.includes("decision:") ||
    lower.includes("routing") ||
    lower.includes("revise") ||
    lower.includes("regenerate") ||
    lower.includes("refining")
  ) {
    return "refining";
  }

  if (
    lower.includes("loading ai model") ||
    lower.includes("loading mistral") ||
    lower.includes("loading writer") ||
    lower.includes("first run")
  ) {
    return "loadingModel";
  }

  if (
    lower.includes("enhancing with ai") ||
    lower.includes("generating") ||
    lower.includes("writing your cv") ||
    lower.includes("writing your cv with ai") ||
    lower.includes("from your data")
  ) {
    return "writing";
  }

  return "working";
}

export { CV_AGENT_BASE, CvAgentApiError, readCvAgentError };
