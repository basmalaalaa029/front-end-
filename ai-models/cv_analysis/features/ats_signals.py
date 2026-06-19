"""Deterministic ATS signals extracted from any CV — fed to the ATS judge prompt."""

from __future__ import annotations

import re
from typing import List, Optional

from cv_analysis.features.feature_engine import _BULLET_RE
from cv_analysis.judges.schemas import CvFacts, StructuredCv
from cv_analysis.parsing.text_pipeline import slice_section

_LINK_LINE_RE = re.compile(
    r"(?:https?://|github\.com|linkedin\.com|gitlab\.com)",
    re.I,
)
_ROLE_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.I)


def _section_body(structured: StructuredCv, key: str, *aliases: str) -> str:
    sec = structured.sections.get(key)
    if sec and sec.body.strip():
        return sec.body.strip()
    return slice_section(structured.raw_markdown, key, *aliases).strip()


def _role_keywords(target_role: str) -> List[str]:
    stop = {"and", "the", "for", "with", "developer", "engineer", "senior", "junior"}
    tokens = [t.lower() for t in _ROLE_TOKEN_RE.findall(target_role or "")]
    return [t for t in tokens if t not in stop and len(t) > 2][:6]


def _keyword_in_both_sections(summary: str, skills: str, keywords: List[str]) -> List[str]:
    if not keywords:
        return []
    summary_l = summary.lower()
    skills_l = skills.lower()
    return [kw for kw in keywords if kw in summary_l and kw in skills_l]


def _keyword_missing_from_section(
    summary: str, skills: str, keywords: List[str],
) -> List[str]:
    missing: List[str] = []
    summary_l = summary.lower()
    skills_l = skills.lower()
    for kw in keywords:
        in_summary = kw in summary_l
        in_skills = kw in skills_l
        if in_summary != in_skills:
            missing.append(kw)
    return missing


def _experience_format_signals(experience_text: str, facts: CvFacts) -> str:
    if not experience_text.strip():
        return "Experience section not detected."
    bullets = len(_BULLET_RE.findall(experience_text))
    lines = [ln.strip() for ln in experience_text.splitlines() if ln.strip()]
    prose_lines = [
        ln for ln in lines
        if not ln.startswith("#") and not _BULLET_RE.match(ln) and len(ln.split()) > 12
    ]
    if bullets == 0 and prose_lines:
        return (
            f"Experience uses paragraph-style lines ({len(prose_lines)} long lines, "
            f"{facts.bullet_count} bullets in full CV) — may confuse ATS parsers."
        )
    if bullets > 0:
        return f"Experience uses bullet lines ({bullets} in section, {facts.bullet_count} in full CV)."
    return "Experience format unclear — check bullet structure for ATS parsing."


def _link_signals(structured: StructuredCv, facts: CvFacts) -> str:
    if not facts.has_links:
        return "No GitHub/LinkedIn/portfolio links detected in extracted text."
    lines: List[str] = []
    header_links = structured.header.get("links", "")
    if header_links:
        lines.append(header_links)
    for key in ("links",):
        body = _section_body(structured, key)
        if body:
            lines.append(body)
    raw = structured.raw_markdown
    for ln in raw.splitlines():
        if _LINK_LINE_RE.search(ln):
            lines.append(ln.strip())
    unique = list(dict.fromkeys(lines))[:4]
    if unique:
        return (
            "Links found as plain text (good for ATS): "
            + " | ".join(unique)
        )
    return "Links detected but format unclear — prefer plain-text URLs, not embedded PDF hyperlinks."


def build_ats_signals(
    structured: StructuredCv,
    facts: CvFacts,
    *,
    filename: str = "",
    target_role: str = "",
    missing_keywords: Optional[List[str]] = None,
) -> str:
    """Build ATS-specific deterministic signals for the judge user prompt."""
    lines = ["ATS SIGNALS (deterministic — use for ATS weaknesses):"]

    if filename.lower().endswith(".pdf"):
        lines.append(
            "- Source file is PDF — some ATS parsers misread PDF layout; "
            "recommend .docx for safer parsing when applying online."
        )
    else:
        lines.append(f"- Source file: {filename or 'text/markdown'} (not PDF).")

    experience = _section_body(structured, "experience", "work history", "employment")
    lines.append(f"- Experience format: {_experience_format_signals(experience, facts)}")

    summary = _section_body(structured, "summary", "professional summary", "profile")
    skills = _section_body(structured, "skills", "technical skills", "technologies")
    role_kws = _role_keywords(target_role or structured.target_role)
    if role_kws:
        in_both = _keyword_in_both_sections(summary, skills, role_kws)
        missing = _keyword_missing_from_section(summary, skills, role_kws)
        if in_both:
            lines.append(f"- Role keywords in BOTH summary and skills: {', '.join(in_both)}")
        if missing:
            lines.append(
                f"- Role keywords not in both summary AND skills: {', '.join(missing)} "
                "(ATS prefers key terms in both places)"
            )

    lines.append(f"- Links: {_link_signals(structured, facts)}")

    if missing_keywords:
        verified = [k for k in missing_keywords[:12] if k.strip()]
        if verified:
            lines.append(
                f"- JD terms to verify in FULL CV TEXT (heuristic): {', '.join(verified)} "
                "(only flag if genuinely absent or too weak to find)"
            )

    return "\n".join(lines)
