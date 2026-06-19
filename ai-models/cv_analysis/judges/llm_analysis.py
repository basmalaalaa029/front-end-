"""Combined ATS+HR judge via llama-server (Path A — single CPU pass)."""

from __future__ import annotations

from hashlib import md5
from typing import Literal, Optional, Tuple

from pydantic import ValidationError

from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.features.ats_signals import build_ats_signals
from cv_analysis.features.cv_inventory import build_cv_inventory, full_cv_text_for_judge
from cv_analysis.judges.cache import LRUCache, get_cache
from cv_analysis.judges.model_runtime import get_analysis_runtime, judge_chat
from cv_analysis.judges.prompts import COMBINED_JUDGE_SYSTEM_CPU, _file_format_label, format_judge_user_message
from cv_analysis.judges.queue import inference_queue
from cv_analysis.judges.schemas import (
    CvFacts,
    EnsembleResult,
    JDContext,
    JudgeOutput,
    KeywordMatchResult,
    StructuredCv,
)
from cv_analysis.judges.issue_cleanup import filter_missing_keywords_for_prompt, prune_judge_output
from cv_analysis.judges.utils import jd_hash, parse_json_robust
from cv_agent.app.config import logger


def _build_facts_prompt(
    structured: StructuredCv,
    facts: CvFacts,
    jd_context: JDContext,
    *,
    compact: bool = False,
    judge_kind: Optional[Literal["ats", "hr"]] = None,
    source_filename: str = "",
    target_role: str = "",
    keyword_result: Optional[KeywordMatchResult] = None,
) -> str:
    inventory = build_cv_inventory(structured, facts, include_section_bodies=False)
    cv_text = full_cv_text_for_judge(structured)

    jd = jd_context.inject_block()
    if compact and len(jd) > 1500:
        jd = jd[:1500]

    role = (target_role or structured.target_role or "Target role").strip()
    raw_missing = (keyword_result.missing_keywords if keyword_result else []) or []
    missing_kws = filter_missing_keywords_for_prompt(cv_text, raw_missing)

    jd_parts = []
    if role and role != "Target role":
        jd_parts.append(f"Target role: {role}")
    if jd.strip():
        jd_parts.append(jd.strip())
    if missing_kws:
        jd_parts.append(
            "JD TERMS TO VERIFY (heuristic only — confirm in FULL CV TEXT before claiming absent):\n"
            f"- May need stronger mention: {', '.join(missing_kws[:12])}"
        )
    job_description = "\n\n".join(jd_parts)

    ats_extra = ""
    if judge_kind == "ats":
        ats_extra = build_ats_signals(
            structured, facts, filename=source_filename, target_role=role,
            missing_keywords=missing_kws,
        )

    experience = structured.sections.get("experience")
    exp_body = experience.body if experience else ""
    has_bullets = facts.bullet_count > 0 or "- " in exp_body or "•" in exp_body

    return format_judge_user_message(
        cv_inventory=inventory,
        file_format=_file_format_label(source_filename),
        has_bullets=has_bullets,
        has_links=facts.has_links,
        has_contact=facts.has_contact,
        job_description=job_description,
        cv_text=cv_text,
        ats_extra=ats_extra,
    )


def _parse_combined_judge(data: dict) -> Tuple[JudgeOutput, JudgeOutput]:
    ats_raw = data.get("ats") if isinstance(data.get("ats"), dict) else data
    hr_raw = data.get("hr") if isinstance(data.get("hr"), dict) else data
    return JudgeOutput(**ats_raw), JudgeOutput(**hr_raw)


def run_combined_judge(
    structured: StructuredCv,
    facts: CvFacts,
    jd_context: JDContext,
    cfg: Optional[CVAnalysisConfig] = None,
    *,
    source_filename: str = "",
    target_role: str = "",
    keyword_result: Optional[KeywordMatchResult] = None,
) -> Tuple[JudgeOutput, JudgeOutput]:
    cfg = cfg or get_cv_analysis_config()
    user_prompt = _build_facts_prompt(
        structured, facts, jd_context, compact=True,
        judge_kind="ats", source_filename=source_filename, target_role=target_role,
        keyword_result=keyword_result,
    )
    system = COMBINED_JUDGE_SYSTEM_CPU
    logger.info("[cv_analysis] Combined judge starting (prompt_chars=%d)…", len(user_prompt))

    runtime = get_analysis_runtime()
    if not runtime.ready:
        fb = JudgeOutput.fallback("CV analysis judge not ready")
        return fb, fb

    for attempt in range(cfg.judge_max_retries):
        try:
            prompt = user_prompt
            if attempt > 0:
                prompt = (
                    'IMPORTANT: Return ONLY JSON with top-level keys "ats" and "hr".\n\n'
                    f"{user_prompt}"
                )
            raw = inference_queue.submit(
                judge_chat, None, system, prompt,
                timeout_s=0,
            )
            d = parse_json_robust(raw)
            if not d:
                raise ValueError("empty parse result")
            ats_out, hr_out = _parse_combined_judge(d)
            cv_text = structured.raw_markdown
            return (
                prune_judge_output(ats_out, cv_text),
                prune_judge_output(hr_out, cv_text),
            )
        except (ValidationError, ValueError, Exception) as exc:
            logger.warning("Combined judge attempt %d/%d failed: %s", attempt + 1, cfg.judge_max_retries, exc)
            if attempt == cfg.judge_max_retries - 1:
                fb = JudgeOutput.fallback(str(exc))
                return fb, fb
    fb = JudgeOutput.fallback("max retries exceeded")
    return fb, fb


def run_llm_analysis(
    structured: StructuredCv,
    facts: CvFacts,
    jd_context: JDContext,
    cfg: Optional[CVAnalysisConfig] = None,
    *,
    keyword_result: Optional[KeywordMatchResult] = None,
    cache_key_prefix: str = "",
    source_filename: str = "",
    target_role: str = "",
    job_description: str = "",
) -> EnsembleResult:
    cfg = cfg or get_cv_analysis_config()
    cv_text = structured.raw_markdown
    cache = get_cache(cfg)
    cv_hash = md5(cv_text.encode()).hexdigest()[:12]
    role = (target_role or structured.target_role or "Target role").strip()
    ctx_h = jd_hash(f"{role}|{(job_description or '').strip()}")
    ens_key = LRUCache.make_key(
        cache_key_prefix or cv_hash, ctx_h, 0, "combined-judge", namespace="judge",
    )
    cached = cache.get(ens_key)
    if cached is not None:
        return cached

    ats_out, hr_out = run_combined_judge(
        structured, facts, jd_context, cfg,
        source_filename=source_filename, target_role=target_role,
        keyword_result=keyword_result,
    )
    logger.info(
        "[cv_analysis] Combined judge done (ATS=%s, HR=%s)",
        ats_out.overall_score, hr_out.overall_score,
    )

    result = EnsembleResult(
        ats_output=ats_out,
        hr_output=hr_out,
        cv_text=cv_text,
    )
    cache.set(ens_key, result)
    return result
