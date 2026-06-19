"""CV analysis feature — schemas for POST /analyze."""

from __future__ import annotations

import json
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class JudgeOutput(BaseModel):
    clarity_score: int = Field(ge=0, le=100, default=0)
    structure_score: int = Field(ge=0, le=100, default=0)
    impact_score: int = Field(ge=0, le=100, default=0)
    skills_relevance_score: int = Field(ge=0, le=100, default=0)
    ats_readiness_score: int = Field(ge=0, le=100, default=0)
    overall_score: int = Field(ge=0, le=100, default=0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses", "improvement_suggestions", "rewrite_suggestions", mode="before")
    @classmethod
    def _coerce_list_of_strings(cls, v):
        if not isinstance(v, list):
            return v
        res = []
        for item in v:
            if isinstance(item, dict):
                res.append(json.dumps(item))
            elif not isinstance(item, str):
                res.append(str(item))
            else:
                res.append(item)
        return res

    @classmethod
    def fallback(cls, reason: str = "parse failure") -> "JudgeOutput":
        """Neutral floor when judge JSON cannot be parsed — avoids misleading 0/100 scores."""
        return cls(
            clarity_score=50,
            structure_score=50,
            impact_score=50,
            skills_relevance_score=50,
            ats_readiness_score=50,
            overall_score=50,
            weaknesses=[f"Judge output could not be parsed: {reason}"],
            improvement_suggestions=[
                "Re-run analysis to refresh recommendations. "
                f"Judge output could not be parsed: {reason}"
            ],
        )

    def lowest_metric(self) -> str:
        m = {
            "Clarity": self.clarity_score,
            "Structure": self.structure_score,
            "Impact": self.impact_score,
            "Skills relevance": self.skills_relevance_score,
            "ATS readiness": self.ats_readiness_score,
        }
        return min(m, key=m.get)  # type: ignore[arg-type]

    def passes(self, threshold: int) -> bool:
        return all(
            v >= threshold for v in [
                self.clarity_score, self.structure_score, self.impact_score,
                self.skills_relevance_score, self.ats_readiness_score,
            ]
        ) and self.overall_score >= threshold


class EnsembleResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True, "revalidate_instances": "never"}
    ats_output: JudgeOutput
    hr_output: JudgeOutput
    cv_text: str = ""


class JDContext(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    canonical_skills: List[str] = Field(default_factory=list)

    def inject_block(self) -> str:
        if not self.keywords:
            return ""
        return (
            f"\n\nJD KEYWORDS: {', '.join(self.keywords[:20])}\n"
            f"Requirements: {'; '.join(self.requirements[:8])}\n"
            f"Canonical skills: {', '.join(self.canonical_skills[:15])}"
        )


class KeywordCoverage(BaseModel):
    name: str
    coverage: int = Field(ge=0, le=100)


class SectionCritique(BaseModel):
    section: str
    status: Literal["pass", "warn", "fail"] = "warn"
    summary: str
    quote: Optional[str] = None
    fix: Optional[str] = None


class AnalysisIssue(BaseModel):
    """One paired issue + recommendation for the Analysis UI."""
    id: int = Field(ge=1)
    title: str
    problem: str
    detail: str = ""
    recommendation: str
    evidence: str = ""
    rewrite: Optional[str] = None
    severity: Literal["gap", "warn"] = "warn"


def judge_issue_triples(scores: JudgeOutput) -> List[tuple[str, str, str]]:
    """Aligned (weakness, suggestion, rewrite) tuples — skips parse-failure lines together."""
    weaknesses = scores.weaknesses or []
    suggestions = scores.improvement_suggestions or []
    rewrites = scores.rewrite_suggestions or []
    triples: List[tuple[str, str, str]] = []
    for i, raw_w in enumerate(weaknesses):
        problem = (raw_w or "").strip()
        if not problem or problem.lower().startswith("judge output could not be parsed"):
            continue
        triples.append((
            problem,
            (suggestions[i] if i < len(suggestions) else "").strip(),
            (rewrites[i] if i < len(rewrites) else "").strip(),
        ))
    return triples


def issues_from_judge(scores: JudgeOutput, limit: int = 8) -> List[AnalysisIssue]:
    """Build UI issue cards directly from LLM judge output (no template layer)."""
    issues: List[AnalysisIssue] = []
    for problem, suggestion, rewrite_raw in judge_issue_triples(scores):
        if len(issues) >= limit:
            break
        recommendation = suggestion or "Update that part of your CV, then run the analysis again."
        title = problem.split(".")[0].strip() or f"Tip {len(issues) + 1}"
        if len(title) > 72:
            title = title[:71].rstrip() + "…"
        issues.append(
            AnalysisIssue(
                id=len(issues) + 1,
                title=title,
                problem=problem,
                detail="",
                recommendation=recommendation,
                evidence="",
                rewrite=rewrite_raw or None,
                severity="gap" if len(issues) < 2 else "warn",
            )
        )
    return issues


class CvSection(BaseModel):
    name: str
    body: str


class StructuredCv(BaseModel):
    raw_markdown: str
    header: Dict[str, str] = Field(default_factory=dict)
    sections: Dict[str, CvSection] = Field(default_factory=dict)
    target_role: str = "Target role"
    company: str = ""


class CvFacts(BaseModel):
    word_count: int = 0
    bullet_count: int = 0
    metrics_count: int = 0
    skills_count: int = 0
    projects_count: int = 0
    experience_roles: int = 0
    has_contact: bool = False
    has_links: bool = False
    sections_present: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)


class KeywordMatchResult(BaseModel):
    coverage: List[KeywordCoverage] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    jd_keywords: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""
    cv_text: str = Field(..., min_length=50)
    job_description: str = ""
    target_role: str = "Target role"
    company: str = ""


class CvParseResult(BaseModel):
    """Metadata extracted from a CV file (role, company, profile context)."""
    target_role: str = ""
    company: str = ""
    job_description: str = ""
    cv_text_length: int = 0
    extraction_word_count: int = 0
    sections_detected: List[str] = Field(default_factory=list)
    bullet_count: int = 0


class AnalysisResult(BaseModel):
    """Structured output for POST /analyze — maps to the dashboard Analysis UI."""
    target_role: str = ""
    company: str = ""
    overall_score: int = Field(ge=0, le=100, default=0)
    ats_score: int = Field(ge=0, le=100, default=0)
    hr_score: int = Field(ge=0, le=100, default=0)
    clarity_score: int = Field(ge=0, le=100, default=0)
    structure_score: int = Field(ge=0, le=100, default=0)
    impact_score: int = Field(ge=0, le=100, default=0)
    skills_relevance_score: int = Field(ge=0, le=100, default=0)
    ats_readiness_score: int = Field(ge=0, le=100, default=0)
    verdict: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)
    issues: List[AnalysisIssue] = Field(default_factory=list)
    keyword_coverage: List[KeywordCoverage] = Field(default_factory=list)
    section_critiques: List[SectionCritique] = Field(default_factory=list)
    jd_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    job_description: str = ""
    extraction_word_count: int = 0
    sections_detected: List[str] = Field(default_factory=list)
    latency_ms: int = 0
    analysis_mode: Literal["ensemble"] = "ensemble"


class PartialAnalysisResult(BaseModel):
    """Phase 1 CPU heuristics — returned before LLM scoring."""
    keyword_coverage: List[KeywordCoverage] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    jd_keywords: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    sections_detected: List[str] = Field(default_factory=list)
    extraction_word_count: int = 0
    structure_score: int = Field(ge=0, le=100, default=0)
    keyword_score: int = Field(ge=0, le=100, default=0)
    format_score: int = Field(ge=0, le=100, default=0)


class AnalysisStartResponse(BaseModel):
    session_id: str
    status: Literal["partial", "pending", "failed"] = "partial"
    partial_result: Optional[PartialAnalysisResult] = None
    error: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    session_id: str
    status: Literal["pending", "partial", "complete", "failed"]
    partial_result: Optional[PartialAnalysisResult] = None
    full_result: Optional[AnalysisResult] = None
    error: Optional[str] = None
    duration_s: Optional[float] = None
    elapsed_s: Optional[float] = None
    progress: Optional[str] = None
