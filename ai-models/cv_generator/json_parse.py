"""Robust JSON parsing for Gemini CV generation responses."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from cv_agent.app.utils import parse_json_robust

_STRING_FIELD_RE = re.compile(
    r'"(summary)"\s*:\s*"((?:[^"\\]|\\.)*)"',
    re.DOTALL,
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


def _repair_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _salvage_cv_json(text: str) -> dict:
    """Best-effort recovery when Gemini returns truncated or malformed CV JSON."""
    result: Dict[str, Any] = {}

    sm = _STRING_FIELD_RE.search(text)
    if sm:
        result["summary"] = sm.group(2).replace('\\"', '"')

    for key in ("weaknesses", "bullets"):
        items = _extract_json_string_list(text, key)
        if items and key == "bullets" and "experience" not in result:
            result.setdefault("experience", [{}])
            if result["experience"]:
                result["experience"][0]["bullets"] = items

    skills_m = re.search(r'"skills"\s*:\s*\{', text, re.I)
    if skills_m:
        skills_blob = text[skills_m.start():]
        end = skills_blob.find("}")
        if end > 0:
            try:
                result["skills"] = json.loads(skills_blob[: end + 1].split(":", 1)[1].strip())
            except json.JSONDecodeError:
                pass

    return result


def parse_cv_json(raw: str) -> dict:
    """Parse Gemini CV JSON with fences, repair, and salvage fallbacks."""
    cleaned = re.sub(r"```(?:json)?", "", raw or "", flags=re.IGNORECASE).replace("```", "").strip()
    if not cleaned:
        raise json.JSONDecodeError("empty response", raw or "", 0)

    for candidate in (cleaned, _repair_trailing_commas(cleaned)):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    parsed = parse_json_robust(cleaned)
    if isinstance(parsed, dict) and parsed:
        return parsed

    for candidate in (cleaned, _repair_trailing_commas(cleaned)):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            blob = candidate[start : end + 1]
            try:
                parsed = json.loads(blob)
                if isinstance(parsed, dict) and parsed:
                    return parsed
            except json.JSONDecodeError:
                salvaged = _salvage_cv_json(blob)
                if salvaged:
                    return salvaged

    raise json.JSONDecodeError("could not parse CV JSON", cleaned, 0)
