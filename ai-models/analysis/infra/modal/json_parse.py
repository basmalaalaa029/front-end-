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
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"', chunk):
        items.append(sm.group(1).replace('\\"', '"'))
        rest = chunk[sm.end():].lstrip()
        if rest.startswith("]"):
            break
    return items


def _salvage_truncated_judge_json(text: str) -> dict:
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
