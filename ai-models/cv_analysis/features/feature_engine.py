"""Layer 4 — CV feature / facts engine."""

from __future__ import annotations

import re
from typing import Dict, List

from cv_analysis.judges.schemas import CvFacts, StructuredCv
from cv_analysis.parsing.text_pipeline import slice_section

_REQUIRED_SECTIONS = ["experience", "education", "skills", "summary"]
_BULLET_RE = re.compile(r"(?m)^\s*(?:[-•*]|\(cid:\d+\))\s+\S")
_METRIC_RE = re.compile(
    r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%|"
    r"\$[\d,]+|"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)\+?x\b|"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)\+?\s*(?:users|customers|clients|products|applications)\b|"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)\+?|"
    r"\d+\s*years?",
    re.I,
)
_CONTACT_RE = re.compile(
    r"\[email\]|\[phone\]|email@|linkedin\.com|@[a-z]+\.[a-z]|\+\d[\d\s\-]{7,}",
    re.I,
)
_LINK_RE = re.compile(r"github\.com|linkedin\.com|portfolio|http", re.I)

_GENERIC_SKILL_LABELS = frozenset({
    "programming",
    "web development",
    "database",
    "computer skills",
    "software development",
    "information technology",
    "it skills",
    "technical skills",
    "computer science",
    "software",
    "technology",
    "communication skills",
    "teamwork",
    "problem solving",
    "leadership",
    "microsoft office",
    "office suite",
    "web design",
    "databases",
})

_SPECIFIC_TECH_PATTERN = re.compile(
    r"\b(?:react|node\.?js|javascript|typescript|python|java|spring|"
    r"angular|vue|django|flask|fastapi|express|mongodb|postgresql|postgres|"
    r"mysql|redis|docker|kubernetes|k8s|aws|azure|gcp|git|graphql|"
    r"html|css|sass|tailwind|next\.?js|rust|go|golang|c\+\+|c#|\.net|"
    r"linux|bash|ci/cd|jenkins|terraform|ansible|figma|sql|nosql|kafka|"
    r"spark|hadoop|tensorflow|pytorch|swift|kotlin|ruby|rails|php|laravel)\b",
    re.I,
)

_VAGUE_PHRASES = (
    "worked on",
    "helped with",
    "was responsible for",
    "involved in",
    "assisted with",
    "participated in",
    "fixed bugs",
    "various tasks",
    "duties included",
    "many things",
    "and so on",
)


def _skill_tokens(skills_section: str) -> List[str]:
    raw = skills_section.replace("\n", ",")
    return [t.strip() for t in raw.split(",") if t.strip()]


def classify_skills(skills_section: str) -> tuple[int, int]:
    """Return (specific_skill_count, generic_skill_count)."""
    tokens = _skill_tokens(skills_section) if skills_section else []
    specific = 0
    generic = 0
    for token in tokens:
        lower = token.lower().strip()
        if not lower:
            continue
        if _SPECIFIC_TECH_PATTERN.search(lower):
            specific += 1
            continue
        if lower in _GENERIC_SKILL_LABELS:
            generic += 1
            continue
        if any(
            phrase in lower
            for phrase in ("development", "programming", "computer", "database", "skills", "technology")
        ):
            generic += 1
            continue
        specific += 1
    return specific, generic


def count_vague_phrases(text: str) -> int:
    lower = text.lower()
    return sum(1 for phrase in _VAGUE_PHRASES if phrase in lower)


def link_flags(text: str) -> Dict[str, bool]:
    lower = text.lower()
    return {
        "github": "github.com" in lower or "gitlab.com" in lower,
        "linkedin": "linkedin.com" in lower,
        "portfolio": bool(
            re.search(r"portfolio|behance\.net|dribbble\.com|\.dev\b|personal site", lower)
        ),
    }


def build_cv_facts(structured: StructuredCv) -> CvFacts:
    """Compute deterministic facts from structured CV — single source of truth for counts."""
    text = structured.raw_markdown
    text_lower = text.lower()

    bullet_count = len(_BULLET_RE.findall(text))
    metrics_count = len(_METRIC_RE.findall(text))
    word_count = len(text.split())

    skills_sec = slice_section(text, "skills", "technical skills", "technologies")
    skill_list = _skill_tokens(skills_sec) if skills_sec else []
    skills_count = len(skill_list)

    projects_sec = slice_section(text, "projects", "portfolio")
    projects_count = max(
        projects_sec.count("###"),
        len([ln for ln in projects_sec.splitlines() if ln.strip() and not ln.strip().startswith("-")]),
        1 if projects_sec.strip() and "project" in text_lower else 0,
    )

    experience_sec = slice_section(text, "experience", "work history", "employment")
    experience_roles = len(re.findall(r"(?m)^###\s+", experience_sec))
    if experience_roles == 0:
        experience_roles = len(
            re.findall(
                r"(?m)^[^\n#•-].*(?:\||–|-).*(?:19|20)\d{2}",
                experience_sec,
            )
        )

    sections_present: List[str] = list(structured.sections.keys())
    missing_sections = [s for s in _REQUIRED_SECTIONS if s not in text_lower]

    return CvFacts(
        word_count=word_count,
        bullet_count=bullet_count,
        metrics_count=metrics_count,
        skills_count=skills_count,
        projects_count=projects_count,
        experience_roles=experience_roles,
        has_contact=bool(_CONTACT_RE.search(text)),
        has_links=bool(_LINK_RE.search(text)),
        sections_present=sections_present,
        missing_sections=missing_sections,
    )
