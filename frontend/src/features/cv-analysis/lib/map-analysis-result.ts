/**
 * Map CV analysis API result to dashboard CvAnalysisResult shape.
 */
import type { AnalysisIssue, CvAnalysisResult } from "../types";

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
  ats?: JudgeBlock;
  hr?: JudgeBlock;
  /** @deprecated Legacy nested shape */
  analysis?: {
    ats?: JudgeBlock;
    hr?: JudgeBlock;
  };
};

const OVERLAP_DROP = 0.72;

function verdictFromScore(score: number): string {
  if (score >= 85) return "Strong match — minor tweaks may still help.";
  if (score >= 70) return "Good fit — a few sections need work before this is recruiter-ready.";
  if (score >= 55) return "Moderate fit — address gaps in skills and keywords for this role.";
  return "Needs significant improvement to align with the job description.";
}

function contentWords(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]{4,}/g) ?? []);
}

function textOverlapRatio(text: string, cvLower: string): number {
  const words = contentWords(text);
  if (words.length < 4) return 0;
  const hits = words.filter((w) => cvLower.includes(w)).length;
  return hits / words.length;
}

function normalizeIssue(text: string): string {
  return text.trim().toLowerCase().replace(/\s+/g, " ");
}

function isNearDuplicate(a: string, b: string): boolean {
  const na = normalizeIssue(a);
  const nb = normalizeIssue(b);
  if (!na || !nb) return false;
  if (na === nb) return true;
  const wa = new Set(contentWords(na));
  const wb = new Set(contentWords(nb));
  if (!wa.size || !wb.size) return false;
  let shared = 0;
  for (const w of wa) {
    if (wb.has(w)) shared += 1;
  }
  return shared / (wa.size + wb.size - shared) >= 0.55;
}

function rewriteContradictsCv(rewrite: string, suggestion: string, cvLower: string): boolean {
  for (const part of [rewrite, suggestion]) {
    if (part.trim() && textOverlapRatio(part, cvLower) >= OVERLAP_DROP) return true;
  }
  return false;
}

function issuesFromJudge(block: JudgeBlock, cvLower?: string): AnalysisIssue[] {
  const issues: AnalysisIssue[] = [];
  const weaknesses = block.weaknesses ?? [];
  const suggestions = block.improvement_suggestions ?? [];
  const rewrites = block.rewrite_suggestions ?? [];
  for (let i = 0; i < weaknesses.length; i++) {
    const problem = (weaknesses[i] ?? "").trim();
    if (!problem || problem.toLowerCase().startsWith("judge output could not be parsed")) continue;
    const recommendation = (suggestions[i] ?? "").trim();
    const rewrite = (rewrites[i] ?? "").trim();
    if (cvLower && rewriteContradictsCv(rewrite, recommendation, cvLower)) continue;
    const title = problem.split(".")[0].trim().slice(0, 72) || `Tip ${issues.length + 1}`;
    issues.push({
      id: issues.length + 1,
      title,
      problem,
      detail: "",
      recommendation: recommendation || "Update that part of your CV, then run analysis again.",
      evidence: "",
      rewrite: rewrite || undefined,
      severity: issues.length < 2 ? "gap" : "warn",
    });
  }
  return issues;
}

function dedupeIssues(issues: AnalysisIssue[]): AnalysisIssue[] {
  const out: AnalysisIssue[] = [];
  for (const issue of issues) {
    if (out.some((existing) => isNearDuplicate(existing.problem, issue.problem))) continue;
    out.push({ ...issue, id: out.length + 1 });
  }
  return out;
}

function dedupeStrings(items: string[]): string[] {
  const out: string[] = [];
  for (const item of items) {
    const text = item.trim();
    if (!text) continue;
    if (out.some((existing) => isNearDuplicate(existing, text))) continue;
    out.push(text);
  }
  return out;
}

function resolveJudges(raw: ApiAnalysisResult): { ats: JudgeBlock; hr: JudgeBlock } {
  const ats = raw.ats ?? raw.analysis?.ats ?? {};
  const hr = raw.hr ?? raw.analysis?.hr ?? {};
  return { ats, hr };
}

export function mapApiResultToCvAnalysis(
  raw: ApiAnalysisResult,
  opts: {
    targetRole?: string;
    company?: string;
    jobDescription?: string;
    cvText?: string;
  } = {},
): CvAnalysisResult {
  const { ats, hr } = resolveJudges(raw);
  const cvLower = opts.cvText?.toLowerCase() ?? "";

  const atsScore = ats.overall_score ?? 0;
  const hrScore = hr.overall_score ?? 0;
  const overall = Math.round((atsScore + hrScore) / 2);

  const strengths = dedupeStrings([...(ats.strengths ?? []), ...(hr.strengths ?? [])]);
  const issues = dedupeIssues([
    ...issuesFromJudge(ats, cvLower || undefined),
    ...issuesFromJudge(hr, cvLower || undefined),
  ]);

  const weaknesses = issues.map((i) => i.problem);
  const improvement_suggestions = issues.map((i) => i.recommendation);
  const rewrite_suggestions = issues.map((i) => i.rewrite ?? "");

  return {
    target_role: opts.targetRole ?? "Target role",
    company: opts.company ?? "",
    job_description: opts.jobDescription ?? "",
    overall_score: overall,
    ats_score: atsScore,
    hr_score: hrScore,
    clarity_score: ats.clarity_score ?? hr.clarity_score ?? 0,
    structure_score: ats.structure_score ?? hr.structure_score ?? 0,
    impact_score: ats.impact_score ?? hr.impact_score ?? 0,
    skills_relevance_score: ats.skills_relevance_score ?? hr.skills_relevance_score ?? 0,
    ats_readiness_score: ats.ats_readiness_score ?? hr.ats_readiness_score ?? 0,
    verdict: verdictFromScore(overall),
    strengths,
    weaknesses,
    improvement_suggestions,
    rewrite_suggestions,
    issues,
    keyword_coverage: [],
    section_critiques: strengths.slice(0, 4).map((s, i) => ({
      section: strengths.length > 1 ? `Strength ${i + 1}` : "Overall",
      status: "pass" as const,
      summary: s,
    })),
    jd_keywords: [],
    missing_keywords: [],
    latency_ms: 0,
    analysis_mode: "ensemble",
  };
}

export const STAGE_LABELS: Record<string, string> = {
  parsing: "Parsing CV…",
  features: "Extracting features and keywords…",
  judging: "AI judge is scoring your CV (CPU: typically 3–10 min for first run)…",
  done: "Finalizing results…",
};
