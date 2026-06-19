"""Generic post-judge validation — works for any CV, no per-issue regex rules."""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from cv_analysis.features.cv_inventory import build_cv_inventory
from cv_analysis.judges.schemas import CvFacts, JudgeOutput, StructuredCv

_ABSENCE_RE = re.compile(
    r"\b(?:missing|not include|does not|doesn't|lack(?:s|ing)?|without|"
    r"not provide|could not find|absent|no mention)\b",
    re.I,
)
_PRESENTATION_RE = re.compile(
    r"\b(?:vague|unclear|weak|generic|could be stronger|could be more|"
    r"not highlight|lacks? impact|lacks? measurable|does not demonstrate|too short|"
    r"could use more|needs more|underwhelming|"
    r"lack(?:s|ing)?\s+(?:measurable|quantifiable|specific|concrete|impact|metrics|detail))\b",
    re.I,
)
_ABSENCE_CLAIM_RE = re.compile(
    r"\b(?:missing|not include|does not include|doesn't include|no mention|absent|"
    r"could not find|not provide)\b",
    re.I,
)
_SECTION_TERMS = frozenset({
    "summary", "education", "experience", "projects", "project",
    "skills", "certifications", "contact",
})
_ENTITY_GENERIC = frozenset({
    "issue", "section", "skills", "experience", "summary", "project",
    "fix", "example", "bullet", "bullets",
})
_SECTION_LABEL_RE = re.compile(
    r"^(?:summary|education|experience|projects?|skills?|certifications?)\s*:\s*",
    re.I,
)
_NUM_TOKEN_RE = re.compile(r"\b\d+\b")
_WORD_RE = re.compile(r"[a-z0-9]{4,}", re.I)
_SHORT_WORD_RE = re.compile(r"[a-z0-9]{3,}", re.I)
_QUOTED_RE = re.compile(r"['\"]([^'\"]{2,60})['\"]")
_LIKE_SUCH_RE = re.compile(
    r"\b(?:like|such as|including|e\.g\.|eg\.)\s+([A-Za-z0-9][\w.+-]*)",
    re.I,
)
_CAP_TOKEN_RE = re.compile(r"\b([A-Z][a-zA-Z]*(?:\.[a-zA-Z]+)?|[A-Z]{2,})\b")

_STOP_TOKENS = frozenset({
    "the", "and", "for", "with", "your", "this", "that", "section", "does", "not",
    "from", "into", "under", "over", "about", "have", "has", "are", "was", "were",
    "job", "title", "role", "skills", "experience", "summary", "education", "project",
    "include", "add", "mention", "specific", "general", "could", "should", "would",
})

# If this much of the suggested fix already appears in the CV, the issue is a false positive.
_OVERLAP_DROP = 0.72
_ABSENCE_OVERLAP_DROP = 0.60
_SEMANTIC_DEDUP_THRESHOLD = 0.55

_GENERIC_CAP_SKIP = frozenset({"CV", "ATS", "HR", "JD", "API", "URL", "PDF"})


def _content_words(text: str, *, min_len: int = 4) -> List[str]:
    cleaned = _SECTION_LABEL_RE.sub("", (text or "").strip())
    cleaned = cleaned.strip("'\"").strip()
    pattern = _SHORT_WORD_RE if min_len < 4 else _WORD_RE
    return [w.lower() for w in pattern.findall(cleaned)]


def text_overlap_ratio(text: str, cv_lower: str, *, min_words: int = 4) -> float:
    """Share of significant words in ``text`` that already appear in the CV."""
    min_len = 3 if min_words < 4 else 4
    words = _content_words(text, min_len=min_len)
    if len(words) < min_words:
        return 0.0
    hits = sum(1 for w in words if w in cv_lower)
    return hits / len(words)


def significant_tokens(text: str) -> Set[str]:
    lower = (text or "").lower()
    tokens = {
        t for t in _SHORT_WORD_RE.findall(lower)
        if t not in _STOP_TOKENS and len(t) > 2
    }
    tokens.update(m.group(0) for m in _NUM_TOKEN_RE.finditer(lower))
    return tokens


def token_jaccard(a: str, b: str) -> float:
    ta, tb = significant_tokens(a), significant_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _discriminative_tokens(tokens: Set[str]) -> Set[str]:
    return {t for t in tokens if t not in _ENTITY_GENERIC and t not in _STOP_TOKENS}


def is_near_duplicate(a: str, b: str, threshold: float = _SEMANTIC_DEDUP_THRESHOLD) -> bool:
    if a.lower().strip() == b.lower().strip():
        return True
    ta, tb = significant_tokens(a), significant_tokens(b)
    shared_disc = _discriminative_tokens(ta) & _discriminative_tokens(tb)
    if len(shared_disc) < 2 and len(ta | tb) <= 4:
        return False
    if token_jaccard(a, b) >= threshold:
        return True
    terms_a = {t.lower() for t in _extract_claimed_terms(a, "")}
    terms_b = {t.lower() for t in _extract_claimed_terms(b, "")}
    shared = terms_a & terms_b
    strong = [
        t for t in shared
        if len(t) >= 4 and t not in _ENTITY_GENERIC and t not in _SECTION_TERMS
    ]
    if strong:
        return True
    return False


def _extract_claimed_terms(weakness: str, suggestion: str) -> List[str]:
    """Pull entity names the model claims are missing (quoted, tech-like, after 'like')."""
    terms: List[str] = []
    seen: Set[str] = set()
    for text in (weakness, suggestion):
        for m in _QUOTED_RE.finditer(text):
            term = m.group(1).strip()
            key = term.lower()
            if key and key not in seen:
                seen.add(key)
                terms.append(term)
        for m in _LIKE_SUCH_RE.finditer(text):
            term = m.group(1).strip().rstrip(".,;")
            key = term.lower()
            if key and key not in seen:
                seen.add(key)
                terms.append(term)
        for m in _CAP_TOKEN_RE.finditer(text):
            token = m.group(1)
            if token in _GENERIC_CAP_SKIP:
                continue
            key = token.lower()
            if key and key not in seen:
                seen.add(key)
                terms.append(token)
    return terms


def _term_in_corpus(term: str, corpus: str) -> bool:
    t = term.lower().strip(".")
    if len(t) < 3:
        return False
    if t in corpus:
        return True
    normalized = t.replace(".", "")
    return normalized in corpus.replace(".", "")


def _is_presentation_quality_issue(weakness: str) -> bool:
    """Presentation/impact issues — not false positives when section names appear in CV."""
    if not _PRESENTATION_RE.search(weakness):
        return False
    return not bool(_ABSENCE_CLAIM_RE.search(weakness))


def claim_contradicts_cv(
    weakness: str,
    suggestion: str,
    cv_lower: str,
    inventory_lower: str,
) -> bool:
    """Drop absence claims when the named entity already appears in CV or inventory."""
    if not _ABSENCE_RE.search(f"{weakness} {suggestion}"):
        return False
    corpus = f"{cv_lower} {inventory_lower}"
    for term in _extract_claimed_terms(weakness, suggestion):
        if term.lower() in _SECTION_TERMS:
            continue
        if _term_in_corpus(term, corpus):
            return True
    return False


def weakness_contradicts_cv(
    weakness: str,
    suggestion: str,
    rewrite: str,
    cv_lower: str,
    *,
    inventory_lower: str = "",
) -> bool:
    """
    Generic false-positive check for any CV:
    - Drop when claimed-missing entities are already in CV/inventory.
    - Drop when the model's own fix/example is already mostly in the CV text.
    - Drop absence claims when suggested text is already present.
    - Keep presentation-quality issues even when rewrite overlaps CV.
    """
    if _is_presentation_quality_issue(weakness):
        return False

    if claim_contradicts_cv(weakness, suggestion, cv_lower, inventory_lower):
        return True

    for part in (rewrite, suggestion):
        if text_overlap_ratio(part, cv_lower) >= _OVERLAP_DROP:
            return True

    combined = f"{weakness} {suggestion}"
    if _ABSENCE_RE.search(combined):
        for part in (rewrite, suggestion, weakness):
            if text_overlap_ratio(part, cv_lower, min_words=2) >= _ABSENCE_OVERLAP_DROP:
                return True

    return False


_GENERIC_REWRITE_PHRASES = (
    "add role keywords",
    "include specific metrics",
    "consider converting",
    "add metrics",
    "improve your cv",
    "update your cv",
)


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _rewrite_looks_generic(rewrite: str) -> bool:
    lower = _normalize_line(rewrite)
    if not lower:
        return True
    return any(phrase in lower for phrase in _GENERIC_REWRITE_PHRASES)


def triple_has_quality_issues(weakness: str, suggestion: str, rewrite: str) -> bool:
    """True when suggestion/rewrite copy each other or rewrite is generic filler."""
    w = _normalize_line(weakness)
    s = _normalize_line(suggestion)
    r = _normalize_line(rewrite)
    if w and w == s:
        return True
    if s and s == r:
        return True
    if rewrite.strip() and _rewrite_looks_generic(rewrite):
        return True
    return False


def audit_judge_output_quality(data: dict) -> List[str]:
    """Return quality issues found in raw judge JSON (single or combined ats/hr)."""
    errors: List[str] = []
    personas = ["ats", "hr"] if isinstance(data.get("ats"), dict) else [None]

    for persona in personas:
        obj = data[persona] if persona else data
        if not isinstance(obj, dict):
            continue
        label = persona or "judge"
        w = obj.get("weaknesses") or []
        s = obj.get("improvement_suggestions") or []
        r = obj.get("rewrite_suggestions") or []

        if not (len(w) == len(s) == len(r)):
            errors.append(f"{label}: array length mismatch {len(w)}/{len(s)}/{len(r)}")

        for i, (wi, si, ri) in enumerate(zip(w, s, r)):
            if _normalize_line(wi) == _normalize_line(si):
                errors.append(f"{label}[{i}]: improvement_suggestions copies weakness verbatim")
            if _normalize_line(si) == _normalize_line(ri):
                errors.append(f"{label}[{i}]: rewrite_suggestions copies improvement verbatim")
            if _rewrite_looks_generic(ri):
                errors.append(f"{label}[{i}]: rewrite_suggestions looks generic, not CV-specific")

    return errors


def _dedupe_issue_triples(
    weaknesses: List[str],
    suggestions: List[str],
    rewrites: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    out_w: List[str] = []
    out_s: List[str] = []
    out_r: List[str] = []
    for w, s, r in zip(weaknesses, suggestions, rewrites):
        if any(is_near_duplicate(w, existing) for existing in out_w):
            continue
        out_w.append(w)
        out_s.append(s)
        out_r.append(r)
    return out_w, out_s, out_r


def validate_judge_output(
    scores: JudgeOutput,
    *,
    cv_text: str,
    structured: Optional[StructuredCv] = None,
    facts: Optional[CvFacts] = None,
) -> JudgeOutput:
    """Remove weaknesses whose fixes contradict the extracted CV text."""
    cv_lower = cv_text.lower()
    inventory_lower = ""
    if structured is not None and facts is not None:
        inventory_lower = build_cv_inventory(
            structured, facts, include_section_bodies=False,
        ).lower()

    weaknesses: List[str] = []
    suggestions: List[str] = []
    rewrites: List[str] = []

    wlist = scores.weaknesses or []
    slist = scores.improvement_suggestions or []
    rlist = scores.rewrite_suggestions or []

    for i, raw_w in enumerate(wlist):
        weakness = (raw_w or "").strip()
        if not weakness:
            continue
        suggestion = (slist[i] if i < len(slist) else "").strip()
        rewrite = (rlist[i] if i < len(rlist) else "").strip()

        if weakness_contradicts_cv(
            weakness, suggestion, rewrite, cv_lower, inventory_lower=inventory_lower,
        ):
            continue

        if triple_has_quality_issues(weakness, suggestion, rewrite):
            continue

        weaknesses.append(weakness)
        suggestions.append(suggestion)
        rewrites.append(rewrite)

    weaknesses, suggestions, rewrites = _dedupe_issue_triples(
        weaknesses, suggestions, rewrites,
    )

    return scores.model_copy(
        update={
            "weaknesses": weaknesses,
            "improvement_suggestions": suggestions,
            "rewrite_suggestions": rewrites,
        }
    )
