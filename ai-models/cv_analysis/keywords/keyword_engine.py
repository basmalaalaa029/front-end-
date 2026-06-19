"""Layer 5 — Keyword matching engine."""

from __future__ import annotations

import re
from typing import List

from cv_analysis.judges.schemas import KeywordCoverage, KeywordMatchResult
from cv_analysis.judges.schemas import JDContext


def _coverage_for_keyword(cv_lower: str, raw: str) -> int:
    name = raw.strip()
    if not name:
        return 0
    key = name.lower()
    if key in cv_lower:
        return 100
    if " " in key:
        parts = [p for p in re.split(r"[\s/|,]+", key) if len(p) > 2]
        if parts:
            hits = sum(1 for p in parts if p in cv_lower)
            return int((hits / len(parts)) * 100)
    return 0


def _is_keyword_present(cv_lower: str, raw: str) -> bool:
    name = raw.strip()
    if not name or len(name) < 2:
        return True
    key = name.lower()
    if key in cv_lower:
        return True
    if " " in key:
        parts = [p for p in re.split(r"[\s/|,]+", key) if len(p) > 2]
        if parts and sum(1 for p in parts if p in cv_lower) >= max(1, len(parts) // 2):
            return True
    return False


def keyword_absent_from_cv(cv_text: str, raw: str) -> bool:
    """True when a JD keyword is not found in CV text (heuristic)."""
    return not _is_keyword_present(cv_text.lower(), raw)


def match_keywords(cv_text: str, jd_context: JDContext, *, limit: int = 30) -> KeywordMatchResult:
    """Extract JD keywords, compute coverage rows and missing keyword list."""
    keywords = list(
        dict.fromkeys(
            (jd_context.keywords or [])
            + (jd_context.canonical_skills or [])
            + (jd_context.requirements or [])[:10]
        )
    )[:limit]

    cv_lower = cv_text.lower()
    coverage: List[KeywordCoverage] = []
    missing: List[str] = []
    seen: set[str] = set()

    for raw in keywords:
        name = raw.strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        cov = _coverage_for_keyword(cv_lower, name)
        coverage.append(KeywordCoverage(name=name, coverage=cov))
        if cov < 100 and not _is_keyword_present(cv_lower, name):
            missing.append(name)

    return KeywordMatchResult(
        coverage=coverage[:24],
        missing_keywords=missing[:12],
        jd_keywords=keywords[:20],
    )
