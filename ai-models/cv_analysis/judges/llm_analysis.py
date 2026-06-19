"""Combined ATS+HR judge via llama-server (Path A — single CPU pass)."""

from __future__ import annotations

from hashlib import md5
from typing import Literal, Optional, Tuple

from pydantic import ValidationError

from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.features.ats_signals import build_ats_signals
from cv_analysis.features.cv_inventory import build_cv_inventory, full_cv_text_for_judge
from cv_analysis.judges.cache import LRUCache, get_cache
from cv_analysis.judges.judge_validation import is_near_duplicate, validate_judge_output
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
from cv_analysis.judges.utils import parse_json_robust
from cv_agent.app.config import logger

MAX_UI_ISSUE_ITEMS = 8


def judge_submit_timeout_s(cfg: CVAnalysisConfig) -> float:
    if cfg.judge_submit_timeout_s > 0:
        return float(cfg.judge_submit_timeout_s)
    return max(600.0, float(cfg.request_timeout_seconds))


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
    missing_kws = (keyword_result.missing_keywords if keyword_result else []) or []

    jd_parts = []
    if role and role != "Target role":
        jd_parts.append(f"Target role: {role}")
    if jd.strip():
        jd_parts.append(jd.strip())
    if missing_kws:
        jd_parts.append(
            "KEYWORD GAPS (from JD match — flag only if truly absent in FULL CV TEXT):\n"
            f"- Missing from CV: {', '.join(missing_kws[:12])}"
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
                timeout_s=judge_submit_timeout_s(cfg),
            )
            d = parse_json_robust(raw)
            if not d:
                raise ValueError("empty parse result")
            ats_out, hr_out = _parse_combined_judge(d)
            ats_out = validate_judge_output(
                ats_out, cv_text=structured.raw_markdown, structured=structured, facts=facts,
            )
            hr_out = validate_judge_output(
                hr_out, cv_text=structured.raw_markdown, structured=structured, facts=facts,
            )
            return ats_out, hr_out
        except (ValidationError, ValueError, Exception) as exc:
            logger.warning("Combined judge attempt %d/%d failed: %s", attempt + 1, cfg.judge_max_retries, exc)
            if attempt == cfg.judge_max_retries - 1:
                fb = JudgeOutput.fallback(str(exc))
                return fb, fb
    fb = JudgeOutput.fallback("max retries exceeded")
    return fb, fb


def _merge_judge_issue_pairs(
    *outputs: JudgeOutput,
    max_items: int = 12,
) -> tuple[list[str], list[str], list[str]]:
    weaknesses: list[str] = []
    suggestions: list[str] = []
    rewrites: list[str] = []
    for out in outputs:
        wlist = out.weaknesses or []
        slist = out.improvement_suggestions or []
        rlist = out.rewrite_suggestions or []
        for i, raw_w in enumerate(wlist):
            if len(weaknesses) >= max_items:
                return weaknesses, suggestions, rewrites
            w = (raw_w or "").strip()
            if not w or w.lower().startswith("judge output could not be parsed"):
                continue
            if any(is_near_duplicate(w, existing) for existing in weaknesses):
                continue
            weaknesses.append(w)
            suggestions.append((slist[i] if i < len(slist) else "").strip())
            rewrites.append((rlist[i] if i < len(rlist) else "").strip())
    return weaknesses, suggestions, rewrites


def _blend_judges(ats_out: JudgeOutput, hr_out: JudgeOutput, cfg: CVAnalysisConfig) -> JudgeOutput:
    w_a = cfg.ats_weight
    w_h = cfg.hr_weight
    total = w_a + w_h or 1.0

    def blend(a: int, h: int) -> int:
        return int(a * w_a / total + h * w_h / total)

    weaknesses, suggestions, rewrites = _merge_judge_issue_pairs(
        ats_out, hr_out, max_items=MAX_UI_ISSUE_ITEMS,
    )

    return JudgeOutput(
        clarity_score=blend(ats_out.clarity_score, hr_out.clarity_score),
        structure_score=blend(ats_out.structure_score, hr_out.structure_score),
        impact_score=blend(ats_out.impact_score, hr_out.impact_score),
        skills_relevance_score=blend(ats_out.skills_relevance_score, hr_out.skills_relevance_score),
        ats_readiness_score=blend(ats_out.ats_readiness_score, hr_out.ats_readiness_score),
        overall_score=blend(ats_out.overall_score, hr_out.overall_score),
        strengths=list(dict.fromkeys(ats_out.strengths + hr_out.strengths))[:6],
        weaknesses=weaknesses,
        improvement_suggestions=suggestions,
        rewrite_suggestions=rewrites,
    )


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
) -> EnsembleResult:
    cfg = cfg or get_cv_analysis_config()
    cv_text = structured.raw_markdown
    cache = get_cache(cfg)
    cv_hash = md5(cv_text.encode()).hexdigest()[:12]
    ens_key = LRUCache.make_key(
        cache_key_prefix or cv_hash, cv_hash, 0, "combined-judge", namespace="judge"
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

    weighted = _blend_judges(ats_out, hr_out, cfg)
    result = EnsembleResult(
        ats_output=ats_out,
        hr_output=hr_out,
        rule_output=weighted,
        weighted=weighted,
        cv_text=cv_text,
    )
    cache.set(ens_key, result)
    return result
