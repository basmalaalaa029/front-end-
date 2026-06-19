"""Layer 2 — Text normalization for CV analysis."""

from __future__ import annotations

import re


def normalize_pdf_artifacts(text: str) -> str:
    """Normalize PDF extraction quirks (bullet glyphs, ligatures, soft hyphens)."""
    if not text:
        return ""
    t = text.replace("\u00ad", "")
    t = re.sub(r"\(cid:\d+\)", "•", t)
    t = re.sub(r"[\uf0b7\uf097\uf095]", "•", t)
    return t


_PAGE_MARKER_RE = re.compile(
    r"^-+\s*\d+\s+of\s+\d+\s*-+$"
    r"|^page\s+\d+(?:\s+of\s+\d+)?\s*$"
    r"|^\d+\s*/\s*\d+\s*$",
    re.I,
)


def _is_page_marker(line: str) -> bool:
    return bool(_PAGE_MARKER_RE.match(line.strip()))


def normalize_raw_text(text: str) -> str:
    """Clean OCR/PDF noise and unify whitespace."""
    if not text:
        return ""

    t = normalize_pdf_artifacts(text)
    t = t.replace("\f", "\n")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\u00a0", " ").replace("\ufeff", "")
    t = re.sub(r"[\u200b-\u200d\ufeff]", "", t)
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in t.split("\n")]
    lines = [ln for ln in lines if ln and not _is_page_marker(ln)]
    return "\n".join(lines)


def is_structured_markdown(text: str) -> bool:
    """True when text already has markdown CV headings from the editor."""
    return bool(re.search(r"(?m)^#{1,3}\s+\S", text.strip()))
