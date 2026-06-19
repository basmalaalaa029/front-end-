"""
cv_agent.utils
==============
Shared utility functions used across the package.

Centralises regex helpers, JSON parsing, timing decorators, and hash functions
so they are defined once and imported everywhere — eliminates duplicate code.
"""

from __future__ import annotations

import json
import re
import time
from functools import wraps
from hashlib import sha256
from typing import Any, Callable, Dict, List

from cv_agent.app.config import logger


_SCORE_FIELD_RE = re.compile(
    r'"(clarity_score|structure_score|impact_score|skills_relevance_score|'
    r'ats_readiness_score|overall_score)"\s*:\s*(\d{1,3})',
    re.I,
)


def _extract_json_string_list(text: str, key: str) -> List[str]:
    """Pull complete quoted strings from a (possibly truncated) JSON array."""
    m = re.search(rf'"{re.escape(key)}"\s*:\s*\[', text, re.I)
    if not m:
        return []
    chunk = text[m.end():]
    items: List[str] = []
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"', chunk):
        items.append(sm.group(1).replace('\\"', '"'))
        rest = chunk[sm.end():].lstrip()
        if rest.startswith("]"):
            break
    return items


def _salvage_truncated_judge_json(text: str) -> dict:
    """Recover scores and complete list items when JSON was cut off mid-generation."""
    scores: Dict[str, int] = {}
    for m in _SCORE_FIELD_RE.finditer(text):
        scores[m.group(1)] = min(100, max(0, int(m.group(2))))
    if len(scores) < 3:
        return {}

    result: Dict[str, Any] = dict(scores)
    for key in ("strengths", "weaknesses", "improvement_suggestions", "rewrite_suggestions"):
        items = _extract_json_string_list(text, key)
        if items:
            result[key] = items

    if "overall_score" not in result and len(scores) >= 3:
        result["overall_score"] = int(sum(scores.values()) / len(scores))

    logger.info(
        "parse_json_robust: salvaged truncated judge JSON (%d scores, %d weaknesses)",
        len(scores),
        len(result.get("weaknesses", [])),
    )
    return result


# ==============================================================================
# TEXT NORMALISATION
# ==============================================================================

def normalise(text: str) -> str:
    """Strip non-alphanumeric characters and lowercase for comparison."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


# ==============================================================================
# ROBUST JSON PARSING
# ==============================================================================

def parse_json_robust(raw: str) -> dict:
    """
    Parse a JSON string with multiple fallback strategies.

    Handles: markdown fences, trailing text, truncated JSON, json_repair library.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()

    for candidate in (cleaned, cleaned.split("\n\n")[0]):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
        blob = match.group()
        for end in range(len(blob), 0, -1):
            try:
                return json.loads(blob[:end])
            except json.JSONDecodeError:
                continue

    try:
        from json_repair import repair_json  # type: ignore[import]
        repaired = repair_json(raw)
        if repaired:
            return json.loads(repaired)
    except (ImportError, json.JSONDecodeError, Exception):
        pass

    salvaged = _salvage_truncated_judge_json(cleaned)
    if salvaged:
        return salvaged

    logger.warning("parse_json_robust: all strategies exhausted for: %.120s", raw)
    return {}


# ==============================================================================
# TIMING DECORATOR — node-level observability
# ==============================================================================

def timed_node(node_name: str) -> Callable:
    """Decorator that logs node start/end with duration in ms."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            t0  = time.perf_counter()
            sid = ""
            if args and hasattr(args[0], "session_id"):
                sid = args[0].session_id
            extra = {"node": node_name, "session_id": sid}
            logger.info("NODE_START", extra=extra)
            try:
                result = fn(*args, **kwargs)
                ms = int((time.perf_counter() - t0) * 1000)
                logger.info("NODE_END", extra={**extra, "duration_ms": ms})
                return result
            except Exception as exc:
                ms = int((time.perf_counter() - t0) * 1000)
                logger.error(
                    "NODE_ERROR: %s", exc,
                    extra={**extra, "duration_ms": ms},
                    exc_info=True,
                )
                raise
        return wrapper
    return decorator


# ==============================================================================
# HASH HELPERS
# ==============================================================================

def jd_hash(jd_text: str) -> str:
    """Short SHA-256 hash of job description text for cache keys."""
    return sha256(jd_text.encode()).hexdigest()[:16]


# ==============================================================================
# MARKDOWN-TO-REPORTLAB HELPER
# ==============================================================================

def md_to_rl(text: str) -> str:
    """Convert basic markdown inline formatting to ReportLab XML tags."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.+?)\*\*',     r'<b>\1</b>',         text)
    text = re.sub(r'\*(.+?)\*',         r'<i>\1</i>',          text)
    text = re.sub(r'_(.+?)_',           r'<i>\1</i>',          text)
    return text
