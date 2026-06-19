"""Deterministic CV inventory — authoritative list of what extraction found."""

from __future__ import annotations

import re

from cv_analysis.features.feature_engine import _METRIC_RE
from cv_analysis.judges.schemas import CvFacts, StructuredCv
from cv_analysis.parsing.text_pipeline import slice_section

_ROLE_LINE_RE = re.compile(
    r"(?m)^(?:###\s+)?([^\n#•-].*(?:\||–|—|-).*(?:19|20)\d{2}[^\n]*)",
)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

# Typical CVs fit comfortably; only truncate very long documents.
_MAX_INVENTORY_BODY = 1200
_MAX_CV_CHARS = 8000


def _section_body(structured: StructuredCv, key: str, *aliases: str) -> str:
    sec = structured.sections.get(key)
    if sec and sec.body.strip():
        return sec.body.strip()
    return slice_section(structured.raw_markdown, key, *aliases).strip()


def _experience_roles(experience_text: str) -> list[str]:
    roles: list[str] = []
    for m in re.finditer(r"(?m)^###\s+(.+)$", experience_text):
        title = m.group(1).strip()
        if title:
            roles.append(title)
    if roles:
        return roles
    for m in _ROLE_LINE_RE.finditer(experience_text):
        line = m.group(1).strip()
        if line and line not in roles:
            roles.append(line)
    return roles


def _metric_snippets(text: str, limit: int = 15) -> list[str]:
    seen: set[str] = set()
    snippets: list[str] = []
    for m in _METRIC_RE.finditer(text):
        s = m.group(0).strip()
        if s and s not in seen:
            seen.add(s)
            snippets.append(s)
        if len(snippets) >= limit:
            break
    return snippets


def build_cv_inventory(
    structured: StructuredCv,
    facts: CvFacts,
    *,
    include_section_bodies: bool = False,
) -> str:
    """Build a plain-text inventory of what is present in the CV (any document).

  When ``include_section_bodies`` is False (default), only metadata and short
  summaries are included — use alongside FULL CV TEXT to avoid prompt bloat.
    """
    lines = [
        "CV INVENTORY (authoritative — extracted from this CV; do NOT claim any item below is missing):",
    ]

    lines.append(f"- Sections present: {', '.join(facts.sections_present) or 'none'}")
    if facts.missing_sections:
        lines.append(f"- Sections not found: {', '.join(facts.missing_sections)}")
    lines.append(f"- Contact info: {'present' if facts.has_contact else 'not detected'}")
    lines.append(f"- Portfolio/GitHub links: {'present' if facts.has_links else 'not detected'}")
    lines.append(
        f"- Bullet lines: {facts.bullet_count}  |  Numbers/metrics detected: {facts.metrics_count}"
    )

    experience = _section_body(structured, "experience", "work history", "employment")
    roles = _experience_roles(experience)
    if roles:
        lines.append("- Job titles / roles found:")
        for role in roles[:8]:
            lines.append(f"  • {role}")

    if not include_section_bodies:
        for key in ("skills", "education", "projects", "certifications", "languages"):
            body = _section_body(structured, key)
            if body:
                preview = body.replace("\n", " ").strip()
                if len(preview) > 120:
                    preview = preview[:120] + "…"
                extra = ""
                if key == "education":
                    years = sorted(set(_YEAR_RE.findall(body)))
                    if years:
                        extra = f" (years: {', '.join(years)})"
                lines.append(f"- {key.title()} section: present{extra} — {preview}")
        metrics = _metric_snippets(structured.raw_markdown)
        if metrics:
            lines.append(f"- Metric tokens found: {', '.join(metrics)}")
        return "\n".join(lines)

    skills = _section_body(structured, "skills", "technical skills", "technologies")
    if skills:
        body = skills[:_MAX_INVENTORY_BODY]
        lines.append(f"- Skills section content:\n{body}")

    education = _section_body(structured, "education", "academic background", "qualifications")
    if education:
        body = education[:_MAX_INVENTORY_BODY]
        years = sorted(set(_YEAR_RE.findall(education)))
        year_note = f" (years found: {', '.join(years)})" if years else ""
        lines.append(f"- Education{year_note}:\n{body}")

    projects = _section_body(structured, "projects", "portfolio")
    if projects:
        body = projects[:_MAX_INVENTORY_BODY]
        lines.append(f"- Projects section content:\n{body}")

    for key in ("certifications", "languages", "links"):
        body = _section_body(structured, key)
        if body:
            lines.append(f"- {key.title()}:\n{body[:600]}")

    metrics = _metric_snippets(structured.raw_markdown)
    if metrics:
        lines.append(f"- Metric tokens found: {', '.join(metrics)}")

    return "\n".join(lines)


def full_cv_text_for_judge(structured: StructuredCv) -> str:
    """Return complete CV text for the judge (no arbitrary mid-document truncation)."""
    text = structured.raw_markdown.strip()
    if len(text) <= _MAX_CV_CHARS:
        return text
    return text[:_MAX_CV_CHARS] + "\n[... truncated for length ...]"
