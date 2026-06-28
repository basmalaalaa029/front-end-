"""Lightweight JSON parse helper for Modal inference (mirrors cv_agent.app.utils)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

_SCORE_FIELD_RE = re.compile(
    r'"(clarity_score|structure_score|impact_score|skills_relevance_score|'
    r'ats_readiness_score|overall_score)"\s*:\s*(\d{1,3})',
    re.I,
)


def _extract_json_string_list(text: str, key: str) -> List[str]:
    m = re.search(rf'"{re.escape(key)}"\s*:\s*\[', text, re.I)
    if not m:
        return []
    chunk = text[m.end():]
    items: List[str] = []
    list_closed = False
    cursor = 0
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"', chunk):
        items.append(sm.group(1).replace('\\"', '"'))
        cursor = sm.end()
        rest = chunk[cursor:].lstrip()
        if rest.startswith("]"):
            list_closed = True
            break

    if not list_closed and items:
        # The list (or its last element) was cut off by a token limit before the
        # closing bracket/quote appeared. The last regex match in that case is
        # usually a half-written fragment (e.g. an unterminated quote swallowing
        # everything up to the next stray `"` later in the raw text) rather than
        # a real, finished item — drop it rather than surface it to the user.
        items.pop()

    return items


def _extract_json_issue_objects(text: str) -> List[dict]:
    """Best-effort extraction of structured issue objects from truncated JSON."""
    m = re.search(r'"issues"\s*:\s*\[', text, re.I)
    if not m:
        return []

    chunk = text[m.end():]
    issues: List[dict] = []

    obj_re = re.compile(
        r'\{\s*"issue"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*'
        r'"whats_wrong"\s*:\s*"((?:[^"\\]|\\.)*)"'
        r'(?:\s*,\s*"what_to_do"\s*:\s*"((?:[^"\\]|\\.)*)")?'
        r'(?:\s*,\s*"example"\s*:\s*"((?:[^"\\]|\\.)*)")?\s*\}',
        re.I | re.S,
    )
    for obj_match in obj_re.finditer(chunk):
        issues.append(
            {
                "issue": obj_match.group(1).replace('\\"', '"'),
                "whats_wrong": obj_match.group(2).replace('\\"', '"'),
                "what_to_do": (obj_match.group(3) or "").replace('\\"', '"'),
                "example": (obj_match.group(4) or "").replace('\\"', '"'),
            }
        )

    return issues


def _salvage_truncated_judge_json(text: str) -> dict:
    scores: Dict[str, int] = {}
    for m in _SCORE_FIELD_RE.finditer(text):
        scores[m.group(1)] = min(100, max(0, int(m.group(2))))
    if len(scores) < 3:
        return {}

    result: Dict[str, Any] = dict(scores)

    issues = _extract_json_issue_objects(text)
    if issues:
        result["issues"] = issues
    else:
        for key in ("strengths", "weaknesses", "improvement_suggestions", "rewrite_suggestions"):
            items = _extract_json_string_list(text, key)
            if items:
                result[key] = items

    strengths = _extract_json_string_list(text, "strengths")
    if strengths:
        result["strengths"] = strengths

    if "overall_score" not in result and len(scores) >= 3:
        result["overall_score"] = int(sum(scores.values()) / len(scores))

    return result


def parse_json_robust(raw: str) -> dict:
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

    return {}
