export type CritiqueStatus = "pass" | "warn" | "fail";

export interface KeywordCoverage {
  name: string;
  coverage: number;
}

export interface SectionCritique {
  section: string;
  status: CritiqueStatus;
  summary: string;
  quote?: string;
  fix?: string;
}

export interface AnalysisIssue {
  id: number;
  title: string;
  problem: string;
  detail: string;
  recommendation: string;
  evidence?: string;
  rewrite?: string;
  severity: "gap" | "warn";
}

/** Legacy shape — kept for cached sessions; new API uses stage polling only. */
export interface PartialAnalysisResult {
  keyword_coverage: KeywordCoverage[];
  missing_keywords: string[];
  jd_keywords: string[];
  missing_sections: string[];
  sections_detected: string[];
  extraction_word_count: number;
  structure_score: number;
  keyword_score: number;
  format_score: number;
}

export interface AnalysisStartResponse {
  job_id: string;
  status: "processing";
}

export interface AnalysisJobResponse {
  job_id: string;
  status: "processing" | "ready" | "failed";
  stage: "parsing" | "features" | "judging" | "done";
  result?: Record<string, unknown>;
  error?: string;
  elapsed_s?: number;
}

export interface CvAnalysisResult {
  target_role: string;
  company: string;
  job_description?: string;
  overall_score: number;
  ats_score?: number;
  hr_score?: number;
  clarity_score: number;
  structure_score: number;
  impact_score: number;
  skills_relevance_score: number;
  ats_readiness_score: number;
  verdict: string;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  rewrite_suggestions: string[];
  issues?: AnalysisIssue[];
  keyword_coverage?: KeywordCoverage[];
  section_critiques: SectionCritique[];
  jd_keywords?: string[];
  missing_keywords?: string[];
  extraction_word_count?: number;
  sections_detected?: string[];
  latency_ms?: number;
  analysis_mode: "model" | "ensemble";
}

export interface AnalyzeCvInput {
  cvText?: string;
  jobDescription?: string;
  targetRole?: string;
  company?: string;
}

/** Passed when opening Analysis (React Router location.state). */
export type AnalysisNavigationState = {
  cvText?: string;
  jobDescription?: string;
  targetRole?: string;
  company?: string;
  /** @deprecated Prefer autoUpload with a pending file. */
  autoRun?: boolean;
  /** Consume a file from pending-upload and run POST /cv-analysis/analyze. */
  autoUpload?: boolean;
  fileSource?: "upload" | "editor";
};
