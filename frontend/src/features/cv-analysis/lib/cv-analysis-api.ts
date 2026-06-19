/**
 * CV analysis API client — POST /cv-analysis/analyze + poll GET /cv-analysis/analyze/{job_id}.
 */
import {
  CV_AGENT_BASE,
  CvAgentClientError,
  cvAgentFetch,
} from "@/shared/lib/cv-agent-client";
import { mapApiResultToCvAnalysis } from "./map-analysis-result";
import type {
  AnalysisJobResponse,
  AnalysisStartResponse,
  AnalyzeCvInput,
  CvAnalysisResult,
} from "../types";

export class CvAnalysisApiError extends CvAgentClientError {
  constructor(message: string, status?: number) {
    super(message, status);
    this.name = "CvAnalysisApiError";
  }
}

const ANALYSIS_POLL_MS = 2000;
const ANALYSIS_MAX_POLL_MS = 25 * 60 * 1000;
const ANALYSIS_POLL_FETCH_TIMEOUT_MS = 30_000;

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const tid = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(tid);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

export const ACTIVE_ANALYSIS_SESSION_KEY = "hub:activeAnalysisJob";

export function saveActiveAnalysisSession(jobId: string): void {
  try {
    sessionStorage.setItem(ACTIVE_ANALYSIS_SESSION_KEY, jobId);
  } catch {
    /* ignore */
  }
}

export function clearActiveAnalysisSession(): void {
  try {
    sessionStorage.removeItem(ACTIVE_ANALYSIS_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function loadActiveAnalysisSession(): string | null {
  try {
    return sessionStorage.getItem(ACTIVE_ANALYSIS_SESSION_KEY);
  } catch {
    return null;
  }
}

export async function startAnalysisJob(
  req: AnalyzeCvInput & { signal?: AbortSignal; file?: File },
): Promise<AnalysisStartResponse> {
  const form = new FormData();
  if (req.file) {
    form.append("file", req.file);
  } else if (req.cvText) {
    form.append("cv_text", req.cvText);
  }
  form.append("jd_text", req.jobDescription ?? "");
  const role = req.targetRole?.trim();
  if (role) {
    form.append("target_role", role);
  }
  return cvAgentFetch<AnalysisStartResponse>("/cv-analysis/analyze", {
    method: "POST",
    body: form,
    signal: req.signal,
  });
}

export async function pollAnalysisJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<AnalysisJobResponse> {
  return cvAgentFetch<AnalysisJobResponse>(`/cv-analysis/analyze/${jobId}`, {
    signal,
    timeoutMs: ANALYSIS_POLL_FETCH_TIMEOUT_MS,
  });
}

async function pollUntilComplete(
  jobId: string,
  opts: AnalyzeCvInput & { signal?: AbortSignal },
  onStatus?: (status: AnalysisJobResponse) => void,
): Promise<CvAnalysisResult> {
  const started = Date.now();
  while (true) {
    if (opts.signal?.aborted) throw new CvAnalysisApiError("Analysis cancelled");
    if (Date.now() - started > ANALYSIS_MAX_POLL_MS) {
      clearActiveAnalysisSession();
      throw new CvAnalysisApiError(
        "Analysis took too long (>25 min). Restart the CV Agent backend and run analysis again.",
      );
    }
    try {
      const status = await pollAnalysisJob(jobId, opts.signal);
      onStatus?.(status);
      if (status.status === "ready" && status.result) {
        clearActiveAnalysisSession();
        return mapApiResultToCvAnalysis(status.result, {
          targetRole: opts.targetRole,
          company: opts.company,
          jobDescription: opts.jobDescription,
          cvText: opts.cvText,
        });
      }
      if (status.status === "failed") {
        clearActiveAnalysisSession();
        throw new CvAnalysisApiError(status.error ?? "Analysis failed");
      }
    } catch (err) {
      if (err instanceof CvAgentClientError && err.status === 404) {
        clearActiveAnalysisSession();
        throw new CvAnalysisApiError(
          "Analysis job expired (backend was restarted). Please run analysis again.",
          404,
        );
      }
      if (err instanceof CvAgentClientError && err.status === 429) {
        await sleep(5000, opts.signal);
        continue;
      }
      throw err;
    }
    await sleep(ANALYSIS_POLL_MS, opts.signal);
  }
}

export async function runAnalysisUploadAsync(
  file: File,
  opts: AnalyzeCvInput & { signal?: AbortSignal } = { cvText: "" },
  _onPartial?: unknown,
  onStatus?: (status: AnalysisJobResponse) => void,
): Promise<CvAnalysisResult> {
  const start = await startAnalysisJob({ ...opts, file });
  if (!start.job_id) {
    throw new CvAnalysisApiError("Analysis failed to start");
  }
  saveActiveAnalysisSession(start.job_id);
  return pollUntilComplete(start.job_id, opts, onStatus);
}

export async function runAnalysisAsync(
  req: AnalyzeCvInput & { signal?: AbortSignal },
  _onPartial?: unknown,
  onStatus?: (status: AnalysisJobResponse) => void,
): Promise<CvAnalysisResult> {
  const start = await startAnalysisJob(req);
  if (!start.job_id) {
    throw new CvAnalysisApiError("Analysis failed to start");
  }
  saveActiveAnalysisSession(start.job_id);
  return pollUntilComplete(start.job_id, req, onStatus);
}

export async function resumeAnalysisAsync(
  jobId: string,
  signal?: AbortSignal,
  onStatus?: (status: AnalysisJobResponse) => void,
): Promise<CvAnalysisResult> {
  return pollUntilComplete(jobId, { signal }, onStatus);
}


export const ANALYSIS_CACHE_KEY = "hub:lastAnalysis";

export type AnalysisFileSource = "upload" | "editor";

export type AnalysisFormInputs = {
  jobDescription: string;
  targetRole: string;
  company: string;
  fileName?: string;
  fileSource?: AnalysisFileSource;
};

export function saveAnalysisCache(
  result: CvAnalysisResult,
  inputs: AnalysisFormInputs,
): void {
  try {
    sessionStorage.setItem(
      ANALYSIS_CACHE_KEY,
      JSON.stringify({ result, inputs, savedAt: Date.now() }),
    );
  } catch {
    /* ignore */
  }
}

export function loadAnalysisCache(): {
  result: CvAnalysisResult;
  inputs: AnalysisFormInputs;
} | null {
  try {
    const raw = sessionStorage.getItem(ANALYSIS_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as {
      result: CvAnalysisResult;
      inputs: AnalysisFormInputs & { cvText?: string };
    };
    if (!parsed.inputs.fileName && parsed.inputs.cvText) {
      parsed.inputs.fileName = "CV.txt";
      parsed.inputs.fileSource = "editor";
    }
    return parsed;
  } catch {
    return null;
  }
}

export { CV_AGENT_BASE };
