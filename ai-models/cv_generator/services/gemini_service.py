"""Gemini API integration for ATS-optimized CV generation."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from cv_agent.app.config import PipelineConfig
from cv_generator.models.cv_schema import CVData
from cv_generator.prompts.cv_generation_prompt import CV_GENERATION_SYSTEM
from cv_generator.json_parse import parse_cv_json
from cv_generator.validation import (
    merge_enhancement,
    validate_enhancement,
    _is_critical_validation_issue,
)

logger = logging.getLogger(__name__)

_model: Any = None
_model_cache_key: str = ""

_FALLBACK_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
)


def _model_candidates(cfg: PipelineConfig) -> list[str]:
    primary = (cfg.gemini_model or "").strip() or _FALLBACK_MODELS[0]
    seen: set[str] = set()
    ordered: list[str] = []
    for name in (primary, *_FALLBACK_MODELS):
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _clear_model_cache() -> None:
    global _model, _model_cache_key
    _model = None
    _model_cache_key = ""


def _get_model(cfg: PipelineConfig, model_name: str) -> Any:
    global _model, _model_cache_key
    api_key = (cfg.gemini_api_key or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    cache_key = f"{api_key}:{model_name}"
    if _model is not None and _model_cache_key == cache_key:
        return _model

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai is not installed: pip install google-generativeai",
        ) from exc

    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=CV_GENERATION_SYSTEM,
        generation_config={
            "temperature": cfg.gemini_temperature,
            "max_output_tokens": cfg.gemini_max_output_tokens,
            "response_mime_type": "application/json",
        },
    )
    _model_cache_key = cache_key
    return _model


def _is_model_not_found_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "404" in text or "not found" in text or "not supported for generatecontent" in text


def _parse_json_response(text: str) -> dict:
    return parse_cv_json(text)


def _build_user_message(user_input: dict) -> str:
    return f"""
Create a complete professional ATS-optimized CV from
this candidate information:

Target Job Title: {user_input.get("target_job", "Not specified")}

PERSONAL INFO:
Name: {user_input.get("full_name")}
Email: {user_input.get("email")}
Phone: {user_input.get("phone")}
Location: {user_input.get("location", "")}
LinkedIn: {user_input.get("linkedin", "")}
GitHub: {user_input.get("github", "")}
Portfolio: {user_input.get("portfolio", "")}

EDUCATION:
{json.dumps(user_input.get("education", []), indent=2)}

EXPERIENCE:
{json.dumps(user_input.get("experience", []), indent=2)}

SKILLS (if empty, extract from experience):
{json.dumps(user_input.get("skills", []), indent=2)}

PROJECTS:
{json.dumps(user_input.get("projects", []), indent=2)}

CERTIFICATIONS:
{json.dumps(user_input.get("certifications", []), indent=2)}

LANGUAGES:
{json.dumps(user_input.get("languages", []), indent=2)}

EXISTING SUMMARY NOTES (rewrite professionally):
{user_input.get("summary_notes", "")}

INSTRUCTIONS:
- If skills list is empty → extract from experience and projects
- Write a professional summary targeting:
  {user_input.get("target_job", "a general tech role")}
- Optimize all content for ATS keyword matching
- Return complete CV as JSON
""".strip()


def _run_gemini(model: Any, user_message: str) -> str:
    response = model.generate_content(user_message)
    return response.text if hasattr(response, "text") else str(response)


async def generate_cv_from_info(
    user_input: dict,
    cfg: Optional[PipelineConfig] = None,
) -> dict:
    """Generate a complete ATS-optimized CV from raw candidate info."""
    cfg = cfg or PipelineConfig()
    user_message = _build_user_message(user_input)

    last_error: Optional[Exception] = None
    last_json_error: Optional[json.JSONDecodeError] = None
    for model_name in _model_candidates(cfg):
        for attempt in range(2):
            try:
                _clear_model_cache()
                model = _get_model(cfg, model_name)
                raw_text = _run_gemini(model, user_message)
                cv_data = _parse_json_response(raw_text)
                if model_name != cfg.gemini_model:
                    logger.info("Gemini generation used fallback model %s", model_name)
                if attempt > 0:
                    logger.info("Gemini JSON parse succeeded on retry")
                return {"status": "success", "cv": cv_data}

            except json.JSONDecodeError as exc:
                last_json_error = exc
                logger.warning(
                    "Gemini invalid JSON (model=%s attempt=%d): %s",
                    model_name, attempt + 1, exc,
                )
                continue

            except Exception as exc:
                last_error = exc
                if _is_model_not_found_error(exc):
                    logger.warning("Gemini model %s unavailable: %s", model_name, exc)
                    break
                logger.error("Gemini API error: %s", exc)
                return {"status": "error", "message": str(exc)}

    if last_json_error:
        logger.error("Gemini returned invalid JSON after retries: %s", last_json_error)
        return {"status": "error", "message": "Generation failed — invalid JSON"}

    message = str(last_error) if last_error else "No Gemini models available"
    return {"status": "error", "message": message}


async def enhance_cv_with_gemini(
    cv_data: CVData,
    cfg: Optional[PipelineConfig] = None,
) -> dict:
    """Generate enhanced CV via Gemini and merge into structured CVData."""
    cfg = cfg or PipelineConfig()
    user_input = cv_data.to_generation_input()

    gen_result = await generate_cv_from_info(user_input, cfg)
    if gen_result.get("status") != "success":
        return {
            "status": gen_result.get("status", "error"),
            "message": gen_result.get("message", "Generation failed"),
            "data": cv_data.model_dump(),
        }

    from cv_generator.validation import normalize_gemini_response

    enhanced_partial = normalize_gemini_response(gen_result["cv"])
    merged = merge_enhancement(cv_data, enhanced_partial)
    issues = validate_enhancement(cv_data, merged)
    critical = [i for i in issues if _is_critical_validation_issue(i)]
    if critical:
        logger.warning("Gemini generation validation failed: %s", critical)
        return {
            "status": "validation_failed",
            "message": "; ".join(critical),
            "data": cv_data.model_dump(),
        }
    if issues:
        logger.warning("Non-critical validation warnings (using enhanced CV): %s", issues)

    return {"status": "success", "data": merged.model_dump(), "cv": enhanced_partial}
