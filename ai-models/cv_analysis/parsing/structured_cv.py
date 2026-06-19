"""Layer 3 — Structured CV extraction from markdown."""

from __future__ import annotations

import re
from typing import Dict, Tuple

from cv_analysis.parsing.normalization import is_structured_markdown, normalize_raw_text
from cv_analysis.judges.schemas import CvSection, StructuredCv
from cv_analysis.parsing.text_pipeline import (
    SECTION_ALIASES,
    _CANONICAL_TITLES,
    _EMAIL_RE,
    _heading_key,
    slice_section,
    structure_cv_text,
)

_LINK_RE = re.compile(
    r"(?:https?://[^\s]+|(?:github|linkedin)\.com/[^\s|]+)",
    re.I,
)
_REQUIRED_SECTIONS = ("summary", "skills", "experience", "education")

_META_SECTION_ALIASES = {
    "summary": (
        "professional summary",
        "summary",
        "profile",
        "about me",
        "objective",
        "career objective",
    ),
    "skills": ("skills", "technical skills", "core competencies", "expertise"),
    "experience": ("experience", "work experience", "employment", "professional experience"),
}


def _meta_section_body(text: str, aliases: Tuple[str, ...]) -> str:
    lines = text.splitlines()
    capture: list[str] = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = re.sub(r"[:\s]+$", "", stripped.lower())
        is_heading = stripped.startswith("#") or any(
            lower == a or lower.startswith(f"{a}:") for a in aliases
        )

        if is_heading:
            heading = re.sub(r"^#+\s*", "", stripped).lower()
            heading = re.sub(r"[:\s]+$", "", heading)
            if any(a in heading or heading == a for a in aliases):
                in_section = True
                continue
            if in_section:
                break
            continue

        if in_section:
            capture.append(stripped)

    return "\n".join(capture).strip()


_ROLE_SEP_RE = re.compile(r"\s*[|–—]\s*|\s{2,}(?=[A-Z])")
_DATE_TAIL_RE = re.compile(
    r"\s*[\(（]?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
    r"|\s*\b(?:19|20)\d{2}\s*[-–—]\s*(?:\d{4}|present|current|now)\b"
    r"|\s*[\(（]\s*(?:19|20)\d{2}[^\)]*[\)）]",
    re.I,
)


def _strip_role_noise(raw: str) -> str:
    """Return just the job title — strip company name and date range."""
    title = _ROLE_SEP_RE.split(raw)[0].strip()
    title = _DATE_TAIL_RE.sub("", title).strip()
    return title


def _first_experience_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            title = stripped[4:].strip()
            if title and title.lower() not in ("role", "education"):
                return _strip_role_noise(title)
        if re.match(r"^##\s+experience", stripped, re.I):
            continue
        if re.search(r"\b(19|20)\d{2}\b", stripped) and re.search(r"[|–—]|-\s", stripped):
            title = _strip_role_noise(stripped)
            if title and title.lower() not in _META_SECTION_ALIASES["summary"]:
                return title
    return ""


def _latest_company(text: str) -> str:
    in_exp = False
    for line in text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("##"):
            in_exp = any(alias in lower for alias in _META_SECTION_ALIASES["experience"])
            continue
        if not in_exp or not stripped.startswith("### "):
            continue
        idx = text.splitlines().index(line)
        for follow in text.splitlines()[idx + 1 : idx + 4]:
            f = follow.strip()
            if not f or f.startswith("#"):
                break
            if "|" in f:
                f = f.split("|", 1)[0]
            if "·" in f:
                parts = [p.strip() for p in f.split("·") if p.strip()]
                if parts:
                    return parts[0]
            if f and not re.match(r"^\d{4}", f):
                return f
    return ""


def extract_cv_metadata(text: str) -> dict[str, str]:
    """Pull role, company, and profile context from CV markdown/plain text."""
    raw = (text or "").strip()
    if not raw:
        return {"target_role": "", "company": "", "job_description": ""}

    target_role = ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    if lines and lines[0].startswith("#"):
        for candidate in lines[1:8]:
            if candidate.startswith("#"):
                break
            if "@" in candidate or "linkedin" in candidate.lower() or re.search(
                r"\+?\d[\d\s().-]{7,}\d", candidate
            ):
                continue
            if candidate.lower() in _META_SECTION_ALIASES["summary"]:
                continue
            target_role = candidate.split("·")[0].strip()
            if target_role:
                break

    if not target_role:
        target_role = _first_experience_title(raw)

    if not target_role:
        for line in lines:
            if "|" in line and re.search(r"\b(19|20)\d{2}\b", line):
                target_role = line.split("|")[0].strip()
                if target_role:
                    break

    if not target_role:
        for pat in (
            r"(?im)^(?:target role|desired role|position sought)[:\s]+(.+)$",
            r"(?im)^(?:title|role)[:\s]+(.+)$",
        ):
            m = re.search(pat, raw)
            if m:
                target_role = m.group(1).strip()
                break

    summary = _meta_section_body(raw, _META_SECTION_ALIASES["summary"])
    skills = _meta_section_body(raw, _META_SECTION_ALIASES["skills"])
    profile_parts = [p for p in (summary, skills) if p]
    job_description = "\n\n".join(profile_parts)

    company = _latest_company(raw)

    return {
        "target_role": target_role.strip() or "Target role",
        "company": company.strip(),
        "job_description": job_description.strip(),
    }


def prepare_markdown(raw: str, *, filename: str = "") -> str:
    """Normalize and structure raw CV text into markdown."""
    if is_structured_markdown(raw):
        return raw.strip()
    text = normalize_raw_text(raw)
    if len(text) < 20:
        return text
    return structure_cv_text(text)


def _extract_header(markdown: str) -> Dict[str, str]:
    header: Dict[str, str] = {}
    lines = [ln.strip() for ln in markdown.splitlines() if ln.strip()]
    if not lines:
        return header

    if lines[0].startswith("#"):
        header["name"] = lines[0].lstrip("#").strip()

    contact_parts: list[str] = []
    links: list[str] = []
    for ln in lines[1:8]:
        if ln.startswith("#"):
            break
        if _LINK_RE.search(ln):
            links.extend(_LINK_RE.findall(ln))
        if _EMAIL_RE.search(ln) or "+" in ln or "linkedin" in ln.lower():
            contact_parts.append(ln)
        elif "name" in header and "role_line" not in header and not ln.startswith("#"):
            if "@" not in ln and "github" not in ln.lower():
                header["role_line"] = ln

    if contact_parts:
        header["contact"] = " | ".join(contact_parts)
    if links:
        header["links"] = " | ".join(dict.fromkeys(links))
    return header


def _build_sections(markdown: str) -> Dict[str, CvSection]:
    sections: Dict[str, CvSection] = {}
    for key in SECTION_ALIASES:
        aliases = SECTION_ALIASES[key]
        body = slice_section(markdown, *aliases)
        if body.strip():
            sections[key] = CvSection(name=_CANONICAL_TITLES[key], body=body.strip())

    header = _extract_header(markdown)
    link_text = header.get("links", "")
    if link_text and "links" not in sections:
        sections["links"] = CvSection(name="Links", body=link_text)
    return sections


def extract_structured_cv(raw: str, *, filename: str = "") -> StructuredCv:
    """Build typed StructuredCv from raw or markdown CV text."""
    markdown = prepare_markdown(raw, filename=filename)
    meta = extract_cv_metadata(markdown)
    header = _extract_header(markdown)
    sections = _build_sections(markdown)

    return StructuredCv(
        raw_markdown=markdown,
        header=header,
        sections=sections,
        target_role=meta["target_role"],
        company=meta["company"],
    )


def profile_context_from_structured(structured: StructuredCv) -> str:
    """Summary + skills text used as profile context / job description fallback."""
    parts = []
    for key in ("summary", "skills"):
        sec = structured.sections.get(key)
        if sec and sec.body.strip():
            parts.append(sec.body.strip())
    return "\n\n".join(parts)
