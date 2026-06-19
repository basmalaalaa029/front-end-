/**
 * Map CV analysis API result to dashboard CvAnalysisResult shape.
 */
import type { AnalysisIssue, CvAnalysisResult, KeywordCoverage } from "../types";

type JudgeBlock = {
  clarity_score?: number;
  structure_score?: number;
  impact_score?: number;
  skills_relevance_score?: number;
  ats_readiness_score?: number;
  overall_score?: number;
  strengths?: string[];
  weaknesses?: string[];
  improvement_suggestions?: string[];
  rewrite_suggestions?: string[];
};

type ApiAnalysisResult = {
  cv_inventory?: string;
  ats_signals?: string;
  keyword_coverage?: {
    coverage?: KeywordCoverage[];
    missing_keywords?: string[];
    jd_keywords?: string[];
  };
  analysis?: {
    ats?: JudgeBlock;
    hr?: JudgeBlock;
    blended?: JudgeBlock;
  };
  latency_ms?: number;
};

function verdictFromScore(score: number): string {
  if (score >= 85) return "Strong match — minor tweaks may still help.";
  if (score >= 70) return "Good fit — a few sections need work before this is recruiter-ready.";
  if (score >= 55) return "Moderate fit — address gaps in skills and keywords for this role.";
  return "Needs significant improvement to align with the job description.";
}

function issuesFromJudge(block: JudgeBlock): AnalysisIssue[] {
  const issues: AnalysisIssue[] = [];
  const weaknesses = block.weaknesses ?? [];
  const suggestions = block.improvement_suggestions ?? [];
  const rewrites = block.rewrite_suggestions ?? [];
  for (let i = 0; i < weaknesses.length && issues.length < 8; i++) {
    const problem = (weaknesses[i] ?? "").trim();
    if (!problem || problem.toLowerCase().startsWith("judge output could not be parsed")) continue;
    const title = problem.split(".")[0].trim().slice(0, 72) || `Tip ${issues.length + 1}`;
    issues.push({
      id: issues.length + 1,
      title,
      problem,
      detail: "",
      recommendation: (suggestions[i] ?? "").trim() || "Update that part of your CV, then run analysis again.",
      evidence: "",
      rewrite: (rewrites[i] ?? "").trim() || undefined,
      severity: issues.length < 2 ? "gap" : "warn",
    });
  }
  return issues;
}

export function mapApiResultToCvAnalysis(
  raw: ApiAnalysisResult,
  opts: { targetRole?: string; company?: string; jobDescription?: string } = {},
): CvAnalysisResult {
  const blended = raw.analysis?.blended ?? raw.analysis?.ats ?? {};
  const ats = raw.analysis?.ats ?? blended;
  const hr = raw.analysis?.hr ?? blended;
  const kw = raw.keyword_coverage ?? {};

  const overall = blended.overall_score ?? ats.overall_score ?? 0;

  return {
    target_role: opts.targetRole ?? "Target role",
    company: opts.company ?? "",
    job_description: opts.jobDescription ?? "",
    overall_score: overall,
    ats_score: ats.overall_score ?? overall,
    hr_score: hr.overall_score ?? overall,
    clarity_score: blended.clarity_score ?? 0,
    structure_score: blended.structure_score ?? 0,
    impact_score: blended.impact_score ?? 0,
    skills_relevance_score: blended.skills_relevance_score ?? 0,
    ats_readiness_score: blended.ats_readiness_score ?? 0,
    verdict: verdictFromScore(overall),
    strengths: blended.strengths ?? [],
    weaknesses: blended.weaknesses ?? [],
    improvement_suggestions: blended.improvement_suggestions ?? [],
    rewrite_suggestions: blended.rewrite_suggestions ?? [],
    issues: issuesFromJudge(blended),
    keyword_coverage: kw.coverage ?? [],
    section_critiques: (blended.strengths ?? []).slice(0, 4).map((s, i) => ({
      section: blended.strengths!.length > 1 ? `Strength ${i + 1}` : "Overall",
      status: "pass" as const,
      summary: s,
    })),
    jd_keywords: kw.jd_keywords ?? [],
    missing_keywords: kw.missing_keywords ?? [],
    extraction_word_count: undefined,
    sections_detected: undefined,
    latency_ms: raw.latency_ms ?? 0,
    analysis_mode: "ensemble",
  };
}

export const STAGE_LABELS: Record<string, string> = {
  parsing: "Parsing CV…",
  features: "Extracting features and keywords…",
  judging: "AI judge is scoring your CV (CPU: typically 3–10 min for first run)…",
  done: "Finalizing results…",
};
