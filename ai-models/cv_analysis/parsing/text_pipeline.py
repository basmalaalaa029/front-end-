"""
Analysis text pipeline
======================
PDF / DOCX / flat text  →  normalized text  →  section-structured markdown  →  analysis.

Flow:
  parse_resume_bytes()        — raw text extraction (file_parsing)
  prepare_cv_for_analysis()   — section detection + markdown structure
  analyze_cv()                — scoring judges
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# Canonical section headings used across analysis heuristics.
SECTION_ALIASES: dict[str, Tuple[str, ...]] = {
    "summary": (
        "professional summary",
        "summary",
        "profile",
        "about me",
        "about",
        "objective",
        "career objective",
        "personal statement",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "tools",
        "expertise",
        "key skills",
    ),
    "experience": (
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "work history",
        "employment history",
    ),
    "education": (
        "education",
        "academic background",
        "qualifications",
        "academics",
    ),
    "projects": (
        "projects",
        "personal projects",
        "portfolio",
        "project experience",
    ),
    "certifications": (
        "certifications",
        "licenses",
        "courses",
        "training",
    ),
    "languages": (
        "languages",
        "language skills",
    ),
}

_CANONICAL_TITLES = {
    "summary": "Professional Summary",
    "skills": "Skills",
    "experience": "Experience",
    "education": "Education",
    "projects": "Projects",
    "certifications": "Certifications",
    "languages": "Languages",
}

_ALL_ALIASES: Tuple[Tuple[str, str], ...] = tuple(
    (canonical, alias)
    for canonical, aliases in SECTION_ALIASES.items()
    for alias in aliases
)

_BULLET_RE = re.compile(r"^\s*(?:[-•*●◦▪▸►]|\d+[.)])\s+")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


from cv_analysis.parsing.normalization import (
    is_structured_markdown,
    normalize_pdf_artifacts,
    normalize_raw_text,
)


def _heading_key(line: str) -> Optional[str]:
    """Map a line to a canonical section key, or None."""
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return None

    # Skill/experience sub-rows like "Frontend:", "Tools:", "Cloud:" — not section headings.
    if re.match(r"^[A-Za-z][A-Za-z\s/&+\-]{0,28}:\s+\S", stripped):
        return None

    core = re.sub(r"^#+\s*", "", stripped)
    core = re.sub(r"[:#.\s]+$", "", core).strip()
    lower = core.lower()

    letters = [c for c in core if c.isalpha()]
    if len(letters) >= 3:
        upper_ratio = sum(c.isupper() for c in letters) / len(letters)
        if upper_ratio >= 0.75:
            lower = core.lower()

    for canonical, aliases in SECTION_ALIASES.items():
        if lower in aliases:
            return canonical
        for alias in aliases:
            if lower.startswith(alias + " ") or lower.startswith(alias + ":"):
                return canonical
    return None


def inject_section_breaks(text: str) -> str:
    """Insert newlines before embedded section headers (single-line PDF dumps only)."""
    if text.count("\n") > 3:
        return text

    out = text
    for canonical, alias in sorted(_ALL_ALIASES, key=lambda x: len(x[1]), reverse=True):
        title = _CANONICAL_TITLES[canonical]
        pattern = rf"(?i)\b({re.escape(alias)})\b\s*:?\s+"
        out = re.sub(pattern, rf"\n\n## {title}\n", out, count=1)
    return out


def _normalize_bullet(line: str) -> str:
    m = _BULLET_RE.match(line)
    if not m:
        return line
    body = _BULLET_RE.sub("", line).strip()
    return f"- {body}" if body else line


def _looks_like_role_header(line: str) -> bool:
    """Detect job title lines inside Experience (e.g. 'Senior Dev | Acme | 2020–2023')."""
    if _heading_key(line) or _BULLET_RE.match(line):
        return False
    if _EMAIL_RE.search(line) or _PHONE_RE.search(line):
        return False
    if len(line) > 100:
        return False
    if re.search(r"\b(19|20)\d{2}\b", line) and ("|" in line or "–" in line or "-" in line):
        return True
    if "|" in line and len(line.split("|")) <= 4:
        return True
    return False


_ROLE_SEPARATORS_RE = re.compile(r"\s*[|–—]\s*|\s{2,}(?=[A-Z])")
_DATE_TAIL_RE = re.compile(
    r"\s*[\(（]?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
    r"|\s*\b(?:19|20)\d{2}\s*[-–—]\s*(?:\d{4}|present|current|now)\b"
    r"|\s*[\(（]\s*(?:19|20)\d{2}[^\)]*[\)）]",
    re.I,
)


def _clean_role_title(line: str) -> str:
    """Extract just the job title from a role header line, stripping company and dates."""
    title = _ROLE_SEPARATORS_RE.split(line)[0].strip()
    title = _DATE_TAIL_RE.sub("", title).strip()
    return title


def structure_cv_text(text: str) -> str:
    """Convert flat PDF/DOCX text into markdown sections for analysis."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if sum(1 for ln in lines if _heading_key(ln)) < 2:
        text = inject_section_breaks(text)

    lines = text.splitlines()
    out: List[str] = []
    in_header = True
    in_experience = False
    header_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        section = _heading_key(stripped)
        if section:
            in_header = False
            in_experience = (section == "experience")
            if header_lines and not out:
                out.extend(_format_header_block(header_lines))
                header_lines.clear()
            out.append(f"## {_CANONICAL_TITLES[section]}")
            continue

        if in_header:
            header_lines.append(stripped)
            continue

        if _BULLET_RE.match(stripped):
            out.append(_normalize_bullet(stripped))
            continue

        # Detect and mark ALL role headers inside the experience section,
        # regardless of what the previous output line was.
        if in_experience and _looks_like_role_header(stripped):
            role_title = _clean_role_title(stripped)
            # Keep the company/date context on the same line after a separator.
            company_part = stripped[len(_ROLE_SEPARATORS_RE.split(stripped)[0]):].strip()
            if company_part:
                out.append(f"### {role_title}")
                out.append(company_part)
            else:
                out.append(f"### {role_title}")
            continue

        out.append(stripped)

    if header_lines and not out:
        out.extend(_format_header_block(header_lines))
    elif header_lines and not any(l.startswith("#") for l in out[:3]):
        out = _format_header_block(header_lines) + out

    return "\n".join(out).strip()


def _format_header_block(lines: List[str]) -> List[str]:
    if not lines:
        return []
    name = lines[0]
    rest = lines[1:]
    block = [f"# {name}"]
    for ln in rest[:4]:
        if _EMAIL_RE.search(ln) or _PHONE_RE.search(ln) or "linkedin" in ln.lower():
            block.append(ln)
        elif not block[1:2]:
            block.append(ln)
        else:
            block.append(ln)
    return block


def prepare_cv_for_analysis(raw: str, *, filename: str = "") -> str:
    """
    Full analysis prep: normalize → detect sections → markdown structure.
    Skips restructuring when input is already editor markdown.
    """
    if is_structured_markdown(raw):
        return raw.strip()

    text = normalize_raw_text(raw)

    if len(text) < 20:
        return text

    return structure_cv_text(text)


def slice_section(cv_text: str, *heading_keywords: str) -> str:
    """
    Return body text under the first section heading matching any keyword.
    Works with markdown (##) and plain PDF headings.
    """
    keywords = [k.lower() for k in heading_keywords]
    lines = cv_text.splitlines()
    capturing = False
    buf: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if capturing:
                buf.append("")
            continue

        if re.match(r"^#{1,3}\s+", stripped):
            level = len(stripped) - len(stripped.lstrip("#"))
            heading = re.sub(r"^#+\s*", "", stripped).strip().lower()
            if any(kw in heading for kw in keywords):
                capturing = True
                continue
            if capturing:
                if level <= 2:
                    break
                buf.append(line)
                continue
            continue

        section = _heading_key(stripped)
        if section:
            title = _CANONICAL_TITLES[section].lower()
            if any(kw in title or kw in SECTION_ALIASES.get(section, ()) for kw in keywords):
                capturing = True
                continue
            if capturing:
                break
            continue

        if capturing:
            buf.append(line)

    return "\n".join(buf).strip()


def parse_cv_file_for_analysis(file_bytes: bytes, filename: str) -> str:
    """Extract bytes → raw text → structured text for analysis."""
    from cv_analysis.parsing.file_parsing import parse_resume_bytes
    from cv_analysis.parsing.structured_cv import extract_structured_cv

    raw = parse_resume_bytes(file_bytes, filename)
    return extract_structured_cv(raw, filename=filename).raw_markdown
