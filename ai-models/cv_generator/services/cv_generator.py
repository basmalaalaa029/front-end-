"""Orchestrate instant template + async Gemini enhancement."""

from __future__ import annotations

import asyncio
import time
from typing import Callable, Optional

from cv_agent.app.config import PipelineConfig, logger
from cv_generator.models.pipeline import JudgeOutput, PipelineResult
from cv_generator.markdown import cv_data_to_markdown
from cv_generator.models.cv_schema import CVData
from cv_generator.services.gemini_service import enhance_cv_with_gemini
from cv_generator.services.template_service import fill_template


def build_template_result(
    cv_data: CVData,
    session_id: str,
    template_markdown: str,
) -> PipelineResult:
    """Build a PipelineResult for the instant template version."""
    filled = sum([
        bool(cv_data.full_name), bool(cv_data.target_role),
        bool(cv_data.email), bool(cv_data.summary),
        bool(cv_data.experience), bool(cv_data.education),
        len(cv_data.skills) >= 3, bool(cv_data.linkedin),
    ])
    base = 55 + round((filled / 8) * 35)
    scores = JudgeOutput(
        clarity_score=min(base + 5, 95),
        structure_score=min(base + 3, 95),
        impact_score=max(base - 5, 50),
        skills_relevance_score=min(base + 2, 95),
        ats_readiness_score=min(base, 90),
        overall_score=base,
        strengths=["Well-structured layout", "Clear section hierarchy"],
        weaknesses=["Template version — AI enhancement pending"],
    )
    return PipelineResult(
        session_id=session_id,
        candidate_name=cv_data.full_name,
        target_role=cv_data.target_role,
        total_iterations=0,
        final_cv=template_markdown,
        template_cv=template_markdown,
        final_scores=scores,
        score_trajectory=[float(base)],
        node_errors=[],
        jd_keywords=[],
        total_latency_ms=0,
    )


async def run_enhancement_background(
    cv_data: CVData,
    session_id: str,
    cfg: PipelineConfig,
    *,
    on_progress: Optional[Callable[[str], None]] = None,
) -> PipelineResult:
    """Run Gemini enhancement and return final PipelineResult."""
    t0 = time.time()
    template = fill_template(cv_data)
    template_md = template["markdown"]

    if on_progress:
        on_progress("Enhancing with AI…")

    ai_result = await enhance_cv_with_gemini(cv_data, cfg)
    node_errors: list[str] = []

    if ai_result.get("status") == "success":
        enhanced = CVData(**ai_result["data"])
        final_md = cv_data_to_markdown(enhanced)
        enhanced_data = ai_result["data"]
    else:
        msg = ai_result.get("message", "AI enhancement failed")
        node_errors.append(msg)
        logger.warning("CV enhancement failed session=%s: %s", session_id, msg)
        enhanced = cv_data
        final_md = template_md
        enhanced_data = None

    elapsed = int((time.time() - t0) * 1000)
    filled = sum([
        bool(cv_data.full_name), bool(cv_data.target_role),
        bool(cv_data.email), bool(cv_data.summary),
        bool(cv_data.experience), bool(cv_data.education),
        len(cv_data.skills) >= 3,
    ])
    base = 60 + round((filled / 7) * 30) if ai_result.get("status") == "success" else 55

    scores = JudgeOutput(
        clarity_score=min(base + 5, 95),
        structure_score=min(base + 3, 95),
        impact_score=min(base + 2, 95) if ai_result.get("status") == "success" else max(base - 5, 50),
        skills_relevance_score=min(base + 2, 95),
        ats_readiness_score=min(base, 90),
        overall_score=base,
        strengths=["Professional wording", "Clear section hierarchy"],
        weaknesses=[] if ai_result.get("status") == "success" else ["AI enhancement unavailable"],
    )

    return PipelineResult(
        session_id=session_id,
        candidate_name=cv_data.full_name,
        target_role=cv_data.target_role,
        total_iterations=1 if ai_result.get("status") == "success" else 0,
        final_cv=final_md,
        template_cv=template_md,
        enhanced_data=enhanced_data,
        final_scores=scores,
        score_trajectory=[float(base)],
        node_errors=node_errors,
        jd_keywords=[],
        total_latency_ms=elapsed,
    )


def run_enhancement_sync(
    cv_data: CVData,
    session_id: str,
    cfg: PipelineConfig,
    *,
    on_progress: Optional[Callable[[str], None]] = None,
) -> PipelineResult:
    """Sync wrapper for thread-pool execution."""
    return asyncio.run(
        run_enhancement_background(cv_data, session_id, cfg, on_progress=on_progress),
    )
