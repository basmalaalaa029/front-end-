"""CV analysis pipeline — parsing → features → keywords/rag → judges → result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.features.feature_engine import build_cv_facts
from cv_analysis.judges.llm_analysis import run_llm_analysis
from cv_analysis.judges.schemas import JDContext, KeywordMatchResult
from cv_analysis.keywords.keyword_engine import match_keywords
from cv_analysis.parsing.file_parsing import parse_resume_bytes
from cv_analysis.parsing.structured_cv import extract_structured_cv, profile_context_from_structured
from cv_analysis.rag.jd_extraction import RAGModule


@dataclass
class AnalysisContext:
    structured: Any
    facts: Any
    jd_context: JDContext
    keyword_result: KeywordMatchResult
    source_filename: str = ""


def _resolve_target_role(explicit: str, detected: str) -> str:
    """Prefer an explicit API/UI role over auto-detected CV metadata."""
    role = (explicit or "").strip()
    if role and role != "Target role":
        return role
    return ((detected or "").strip() or "Target role")


def _apply_target_role(structured: Any, target_role: str) -> str:
    role = _resolve_target_role(target_role, structured.target_role)
    structured.target_role = role
    return role


def prepare_cv_from_bytes(
    file_bytes: bytes,
    filename: str,
    cfg: Optional[CVAnalysisConfig] = None,
    *,
    target_role: str = "Target role",
) -> AnalysisContext:
    cfg = cfg or get_cv_analysis_config()
    raw = parse_resume_bytes(file_bytes, filename)
    structured = extract_structured_cv(raw, filename=filename)
    role = _apply_target_role(structured, target_role)
    facts = build_cv_facts(structured)
    rag = RAGModule(cfg.ontology_path)
    profile = profile_context_from_structured(structured)
    jd_context = rag.extract(profile, role, cfg)
    keyword_result = match_keywords(structured.raw_markdown, jd_context)
    return AnalysisContext(
        structured=structured,
        facts=facts,
        jd_context=jd_context,
        keyword_result=keyword_result,
        source_filename=filename,
    )


def prepare_cv_from_text(
    cv_text: str,
    *,
    target_role: str = "Target role",
    job_description: str = "",
    cfg: Optional[CVAnalysisConfig] = None,
) -> AnalysisContext:
    cfg = cfg or get_cv_analysis_config()
    structured = extract_structured_cv(cv_text)
    role = _apply_target_role(structured, target_role)
    facts = build_cv_facts(structured)
    rag = RAGModule(cfg.ontology_path)
    jd = job_description or profile_context_from_structured(structured)
    jd_context = rag.extract(jd, role, cfg)
    keyword_result = match_keywords(structured.raw_markdown, jd_context)
    return AnalysisContext(
        structured=structured,
        facts=facts,
        jd_context=jd_context,
        keyword_result=keyword_result,
    )


def run_analysis_pipeline(
    *,
    cv_text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: str = "resume.pdf",
    job_description: str = "",
    target_role: str = "Target role",
    cfg: Optional[CVAnalysisConfig] = None,
    on_stage: Optional[callable] = None,
) -> Dict[str, Any]:
    """Run judges and return only model ATS + HR outputs."""
    cfg = cfg or get_cv_analysis_config()

    if on_stage:
        on_stage("parsing")

    if file_bytes is not None:
        ctx = prepare_cv_from_bytes(
            file_bytes, filename, cfg=cfg, target_role=target_role,
        )
    elif cv_text is not None:
        ctx = prepare_cv_from_text(
            cv_text, target_role=target_role, job_description=job_description, cfg=cfg,
        )
    else:
        raise ValueError("Provide cv_text or file_bytes.")

    text = ctx.structured.raw_markdown
    if len(text.strip()) < 50:
        raise ValueError("CV text is too short — provide at least 50 characters.")

    if on_stage:
        on_stage("features")

    role = _resolve_target_role(target_role, ctx.structured.target_role)
    ctx.structured.target_role = role

    if job_description.strip():
        rag = RAGModule(cfg.ontology_path)
        ctx.jd_context = rag.extract(job_description, role, cfg)
        ctx.keyword_result = match_keywords(ctx.structured.raw_markdown, ctx.jd_context)

    if on_stage:
        on_stage("judging")

    ensemble = run_llm_analysis(
        ctx.structured, ctx.facts, ctx.jd_context, cfg,
        keyword_result=ctx.keyword_result,
        source_filename=ctx.source_filename,
        target_role=role,
        job_description=job_description,
    )

    return {
        "ats": ensemble.ats_output.model_dump(),
        "hr": ensemble.hr_output.model_dump(),
    }
