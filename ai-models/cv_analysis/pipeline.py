"""CV analysis pipeline — parsing → features → keywords/rag → judges → result."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.features.ats_signals import build_ats_signals
from cv_analysis.features.cv_inventory import build_cv_inventory
from cv_analysis.features.feature_engine import build_cv_facts
from cv_analysis.judges.llm_analysis import run_llm_analysis
from cv_analysis.judges.schemas import JDContext, KeywordMatchResult
from cv_analysis.keywords.keyword_engine import match_keywords
from cv_analysis.parsing.file_parsing import parse_resume_bytes
from cv_analysis.parsing.structured_cv import extract_structured_cv, profile_context_from_structured
from cv_analysis.rag.jd_extraction import RAGModule
from cv_agent.app.config import logger


@dataclass
class AnalysisContext:
    structured: Any
    facts: Any
    jd_context: JDContext
    keyword_result: KeywordMatchResult
    source_filename: str = ""


def prepare_cv_from_bytes(
    file_bytes: bytes,
    filename: str,
    cfg: Optional[CVAnalysisConfig] = None,
) -> AnalysisContext:
    cfg = cfg or get_cv_analysis_config()
    raw = parse_resume_bytes(file_bytes, filename)
    structured = extract_structured_cv(raw, filename=filename)
    facts = build_cv_facts(structured)
    rag = RAGModule(cfg.ontology_path)
    profile = profile_context_from_structured(structured)
    jd_context = rag.extract(profile, structured.target_role, cfg)
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
    if structured.target_role == "Target role" and target_role != "Target role":
        structured.target_role = target_role
    facts = build_cv_facts(structured)
    rag = RAGModule(cfg.ontology_path)
    jd = job_description or profile_context_from_structured(structured)
    jd_context = rag.extract(jd, structured.target_role, cfg)
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
    """Full pipeline returning the new API result shape."""
    cfg = cfg or get_cv_analysis_config()
    t0 = time.perf_counter()

    if on_stage:
        on_stage("parsing")

    if file_bytes is not None:
        ctx = prepare_cv_from_bytes(file_bytes, filename, cfg=cfg)
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

    cv_inventory = build_cv_inventory(ctx.structured, ctx.facts)
    ats_signals = build_ats_signals(
        ctx.structured, ctx.facts,
        filename=ctx.source_filename,
        target_role=ctx.structured.target_role,
        missing_keywords=ctx.keyword_result.missing_keywords,
    )

    if job_description.strip():
        rag = RAGModule(cfg.ontology_path)
        ctx.jd_context = rag.extract(job_description, ctx.structured.target_role, cfg)
        ctx.keyword_result = match_keywords(ctx.structured.raw_markdown, ctx.jd_context)

    if on_stage:
        on_stage("judging")

    role = (target_role or "").strip() or ctx.structured.target_role
    ensemble = run_llm_analysis(
        ctx.structured, ctx.facts, ctx.jd_context, cfg,
        keyword_result=ctx.keyword_result,
        source_filename=ctx.source_filename,
        target_role=role,
    )

    latency_ms = int((time.perf_counter() - t0) * 1000)
    logger.info("[cv_analysis] Pipeline complete in %dms", latency_ms)

    return {
        "cv_inventory": cv_inventory,
        "ats_signals": ats_signals,
        "keyword_coverage": {
            "coverage": [k.model_dump() for k in ctx.keyword_result.coverage],
            "missing_keywords": ctx.keyword_result.missing_keywords,
            "jd_keywords": ctx.keyword_result.jd_keywords,
        },
        "analysis": {
            "ats": ensemble.ats_output.model_dump(),
            "hr": ensemble.hr_output.model_dump(),
            "blended": ensemble.weighted.model_dump(),
        },
        "latency_ms": latency_ms,
    }
