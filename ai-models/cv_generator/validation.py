"""Post-enhancement validation — immutable fields and metric invention checks."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from cv_generator.models.cv_schema import CVData, Experience, Project

_NUMERIC_RE = re.compile(
    r"\b\d{1,3}(?:,\d{3})+(?:\+)?%?\b"
    r"|\b\d+(?:\.\d+)?%+\b"
    r"|\b\d{2,}(?:\+)?%?\b",
)

_SKILL_CATEGORIES = ("frontend", "backend", "databases", "tools", "cloud")


def extract_significant_metrics(text: str) -> set[str]:
    """Impact-style numbers only — ignores bare 1-9 and bare 4-digit years."""
    out: set[str] = set()
    for m in _NUMERIC_RE.finditer(text or ""):
        raw = m.group(0)
        token = raw.replace(",", "").rstrip("%+")
        if len(token) == 4 and token.startswith(("19", "20")):
            continue
        if raw.endswith("%"):
            out.add(f"{token}%")
        elif raw.endswith("+"):
            out.add(f"{token}+")
        else:
            out.add(token)
    return out


def extract_numeric_tokens(text: str) -> set[str]:
    return extract_significant_metrics(text)


def _collect_source_metrics(cv: CVData) -> set[str]:
    parts: List[str] = [cv.summary]
    for exp in cv.experience:
        parts.extend(exp.bullets)
    for proj in cv.projects:
        parts.extend(_project_text_parts(proj))
    for edu in cv.education:
        if edu.gpa:
            parts.append(f"GPA {edu.gpa}")
    return extract_significant_metrics(" ".join(parts))


def categorize_skills_field(skills_field: Any) -> Optional[Dict[str, List[str]]]:
    """Extract categorized skills dict from Gemini JSON (all category keys)."""
    if not isinstance(skills_field, dict):
        return None
    out: Dict[str, List[str]] = {}
    for key, raw in skills_field.items():
        if not isinstance(raw, list):
            continue
        items = [str(item).strip() for item in raw if str(item).strip()]
        if items:
            out[str(key)] = items
    return out or None


def flatten_skills_field(skills_field: Any) -> List[str]:
    """Normalize flat list or categorized skills dict from Gemini JSON."""
    if isinstance(skills_field, list):
        return [str(s).strip() for s in skills_field if str(s).strip()]
    if isinstance(skills_field, dict):
        out: List[str] = []
        for items in skills_field.values():
            if not isinstance(items, list):
                continue
            for item in items:
                label = str(item).strip()
                if label and label not in out:
                    out.append(label)
        return out
    return []


def _experience_identity_key(exp: Experience) -> Tuple[str, str, str, str]:
    return (
        exp.job_title.strip().lower(),
        exp.company.strip().lower(),
        exp.start_date.strip(),
        exp.end_date.strip(),
    )


def _project_identity_key(proj: Project) -> Tuple[str, str]:
    return (proj.name.strip().lower(), proj.tech_used.strip().lower())


def _experience_dict_identity_key(enh: dict) -> Tuple[str, str, str, str]:
    return (
        str(enh.get("job_title", "")).strip().lower(),
        str(enh.get("company", "")).strip().lower(),
        str(enh.get("start_date", "")).strip(),
        str(enh.get("end_date", "")).strip(),
    )


def _project_dict_identity_key(enh: dict) -> Tuple[str, str]:
    return (
        str(enh.get("name", "")).strip().lower(),
        str(enh.get("tech_used", "")).strip().lower(),
    )


def normalize_gemini_response(partial: dict) -> dict:
    """Flatten nested Gemini JSON into the shape expected by merge_enhancement."""
    if not isinstance(partial, dict):
        return {}

    data = dict(partial)
    nested = data.pop("personal_info", None)
    if isinstance(nested, dict):
        for key in ("full_name", "email", "phone", "location", "linkedin", "github", "portfolio"):
            if nested.get(key) and not data.get(key):
                data[key] = nested[key]

    for alias in ("professional_summary", "summary_notes"):
        if not data.get("summary") and data.get(alias):
            data["summary"] = data[alias]

    if isinstance(data.get("cv"), dict):
        inner = normalize_gemini_response(data["cv"])
        data = {**inner, **{k: v for k, v in data.items() if k != "cv" and v}}

    return data


def _project_text_parts(proj: Project) -> List[str]:
    parts = list(proj.bullets)
    if proj.description:
        parts.append(proj.description)
    return parts


def validate_immutable_fields(original: CVData, enhanced: CVData) -> List[str]:
    """Return issues when identity fields were changed by the model."""
    issues: List[str] = []

    if original.full_name.strip() != enhanced.full_name.strip():
        issues.append("full_name was modified")
    if original.email.strip() != enhanced.email.strip():
        issues.append("email was modified")

    orig_exp = {_experience_identity_key(e): e for e in original.experience}
    enh_exp = {_experience_identity_key(e): e for e in enhanced.experience}
    if set(orig_exp) != set(enh_exp):
        issues.append("experience identity fields (title/company/dates) were modified")

    orig_proj = {_project_identity_key(p): p for p in original.projects}
    enh_proj = {_project_identity_key(p): p for p in enhanced.projects}
    if set(orig_proj) != set(enh_proj):
        issues.append("project identity fields (name/tech) were modified")

    return issues


def validate_no_invented_metrics(original: CVData, enhanced: CVData) -> List[str]:
    """Flag impact metrics in enhanced text that were not in the source."""
    source_nums = _collect_source_metrics(original)

    issues: List[str] = []
    for exp in enhanced.experience:
        for i, bullet in enumerate(exp.bullets):
            new_nums = extract_significant_metrics(bullet) - source_nums
            if new_nums:
                issues.append(
                    f"invented metrics {sorted(new_nums)} in experience bullet {i + 1}",
                )
    for proj in enhanced.projects:
        for part in _project_text_parts(proj):
            new_nums = extract_significant_metrics(part) - source_nums
            if new_nums:
                issues.append(f"invented metrics {sorted(new_nums)} in project {proj.name}")

    summary_new = extract_significant_metrics(enhanced.summary) - source_nums
    if summary_new:
        issues.append(f"invented metrics {sorted(summary_new)} in summary")

    return issues


def _is_critical_validation_issue(issue: str) -> bool:
    return "identity" in issue or "modified" in issue


def validate_enhancement(original: CVData, enhanced: CVData) -> List[str]:
    """Run all enhancement quality checks."""
    return validate_immutable_fields(original, enhanced) + validate_no_invented_metrics(
        original, enhanced,
    )


def merge_enhancement(original: CVData, enhanced_partial: dict) -> CVData:
    """
    Merge Gemini JSON into original CVData.
    Identity fields always come from original; only prose fields may change.
    """
    enhanced_partial = normalize_gemini_response(enhanced_partial)
    data = original.model_dump()

    if enhanced_partial.get("summary"):
        data["summary"] = str(enhanced_partial["summary"]).strip()

    categorized = categorize_skills_field(enhanced_partial.get("skills"))
    flat_skills = flatten_skills_field(enhanced_partial.get("skills"))
    if categorized:
        data["skills_by_category"] = categorized
    if flat_skills:
        data["skills"] = flat_skills
    elif not original.skills:
        data["skills"] = []

    if isinstance(enhanced_partial.get("experience"), list):
        enh_list = enhanced_partial["experience"]
        enh_by_key: Dict[Tuple[str, str, str, str], dict] = {}
        enh_by_index: List[dict] = []
        for item in enh_list:
            if isinstance(item, dict):
                enh_by_key[_experience_dict_identity_key(item)] = item
                enh_by_index.append(item)
        merged_exp: List[dict] = []
        for i, orig_exp in enumerate(original.experience):
            entry = orig_exp.model_dump()
            enh = enh_by_key.get(_experience_identity_key(orig_exp))
            if enh is None and i < len(enh_by_index):
                enh = enh_by_index[i]
            if isinstance(enh, dict) and enh.get("bullets"):
                entry["bullets"] = [
                    str(b).strip() for b in enh["bullets"] if str(b).strip()
                ]
            merged_exp.append(entry)
        data["experience"] = merged_exp

    if isinstance(enhanced_partial.get("projects"), list):
        enh_list = enhanced_partial["projects"]
        enh_by_key: Dict[Tuple[str, str], dict] = {}
        enh_by_index: List[dict] = []
        for item in enh_list:
            if isinstance(item, dict):
                enh_by_key[_project_dict_identity_key(item)] = item
                enh_by_index.append(item)
        merged_proj: List[dict] = []
        for i, orig_proj in enumerate(original.projects):
            entry = orig_proj.model_dump()
            enh = enh_by_key.get(_project_identity_key(orig_proj))
            if enh is None and i < len(enh_by_index):
                enh = enh_by_index[i]
            if isinstance(enh, dict):
                bullets = [
                    str(b).strip() for b in (enh.get("bullets") or []) if str(b).strip()
                ]
                if bullets:
                    entry["bullets"] = bullets
                    entry["description"] = ""
                elif enh.get("description"):
                    entry["description"] = str(enh["description"]).strip()
                    entry["bullets"] = []
            merged_proj.append(entry)
        data["projects"] = merged_proj

    if isinstance(enhanced_partial.get("education"), list) and enhanced_partial["education"]:
        merged_edu: List[dict] = []
        for i, orig_edu in enumerate(original.education):
            entry = orig_edu.model_dump()
            if i < len(enhanced_partial["education"]):
                enh = enhanced_partial["education"][i]
                if isinstance(enh, dict):
                    for field in ("degree", "university", "year", "gpa"):
                        if enh.get(field):
                            entry[field] = str(enh[field]).strip()
            merged_edu.append(entry)
        data["education"] = merged_edu

    if enhanced_partial.get("certifications"):
        ai_certs = [
            str(c).strip() for c in enhanced_partial["certifications"] if str(c).strip()
        ]
        orig_certs = [str(c).strip() for c in (original.certifications or []) if str(c).strip()]
        data["certifications"] = list(dict.fromkeys(orig_certs + ai_certs))
    elif original.certifications:
        data["certifications"] = list(original.certifications)

    if enhanced_partial.get("languages"):
        data["languages"] = [
            str(lang).strip() for lang in enhanced_partial["languages"] if str(lang).strip()
        ]

    return CVData(**data)
