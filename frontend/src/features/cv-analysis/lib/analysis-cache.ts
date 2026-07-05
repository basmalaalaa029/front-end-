import { useAuthStore } from "@/features/auth/stores/auth-store";
import type { CvAnalysisResult } from "@/features/cv-analysis/types";

const ANALYSIS_CACHE_BASE = "hub:lastAnalysis";
const ACTIVE_ANALYSIS_SESSION_BASE = "hub:activeAnalysisJob";

export type AnalysisFileSource = "upload" | "editor";

export type AnalysisFormInputs = {
  jobDescription: string;
  targetRole: string;
  company: string;
  fileName?: string;
  fileSource?: AnalysisFileSource;
  cvText?: string;
};

type AnalysisCachePayload = {
  result: CvAnalysisResult;
  inputs: AnalysisFormInputs;
  savedAt: number;
};

function userSuffix(): string {
  return useAuthStore.getState().user?._id ?? "guest";
}

function analysisCacheKey(): string {
  return `${ANALYSIS_CACHE_BASE}:${userSuffix()}`;
}

function activeSessionKey(): string {
  return `${ACTIVE_ANALYSIS_SESSION_BASE}:${userSuffix()}`;
}

export function saveAnalysisCache(
  result: CvAnalysisResult,
  inputs: AnalysisFormInputs,
): void {
  try {
    const payload: AnalysisCachePayload = {
      result,
      inputs,
      savedAt: Date.now(),
    };
    localStorage.setItem(analysisCacheKey(), JSON.stringify(payload));
  } catch {
    /* ignore */
  }
}

export function loadAnalysisCache(): {
  result: CvAnalysisResult;
  inputs: AnalysisFormInputs;
} | null {
  try {
    const raw = localStorage.getItem(analysisCacheKey());
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AnalysisCachePayload;
    if (!parsed?.result) return null;
    const inputs = { ...parsed.inputs };
    if (!inputs.fileName && inputs.cvText) {
      inputs.fileName = "CV.txt";
      inputs.fileSource = "editor";
    }
    return { result: parsed.result, inputs };
  } catch {
    return null;
  }
}

export function clearAnalysisCache(): void {
  try {
    localStorage.removeItem(analysisCacheKey());
  } catch {
    /* ignore */
  }
}

export function saveActiveAnalysisSession(jobId: string): void {
  try {
    localStorage.setItem(activeSessionKey(), jobId);
  } catch {
    /* ignore */
  }
}

export function clearActiveAnalysisSession(): void {
  try {
    localStorage.removeItem(activeSessionKey());
  } catch {
    /* ignore */
  }
}

export function loadActiveAnalysisSession(): string | null {
  try {
    return localStorage.getItem(activeSessionKey());
  } catch {
    return null;
  }
}

/** Migrate legacy sessionStorage cache for the signed-in user (one-time). */
export function migrateLegacyAnalysisCache(): void {
  try {
    const legacyKey = "hub:lastAnalysis";
    const legacy = sessionStorage.getItem(legacyKey);
    if (!legacy) return;
    if (!localStorage.getItem(analysisCacheKey())) {
      localStorage.setItem(analysisCacheKey(), legacy);
    }
    sessionStorage.removeItem(legacyKey);
  } catch {
    /* ignore */
  }
}
