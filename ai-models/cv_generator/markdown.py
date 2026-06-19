"""Convert structured CVData to ATS-friendly Markdown."""

from __future__ import annotations

from typing import Dict, List

from cv_generator.models.cv_schema import CVData, Experience

_SKILL_LABELS: Dict[str, str] = {
    "frontend": "Frontend",
    "backend": "Backend",
    "databases": "Databases",
    "tools": "Tools",
    "cloud": "Cloud",
}


def cv_data_to_markdown(cv: CVData) -> str:
    """Build body-only ATS markdown (no name/contact — header supplied separately)."""
    lines: List[str] = []

    if cv.summary:
        lines += ["## Professional Summary", cv.summary]

    skills_lines = _format_skills_section(cv)
    if skills_lines:
        lines += ["", *skills_lines]

    if cv.experience:
        lines += ["", "## Work Experience"]
        for exp in cv.experience:
            lines += _format_experience_block(exp)

    if cv.projects:
        lines += ["", "## Projects"]
        for proj in cv.projects:
            lines.append("")
            header = proj.name
            if proj.tech_used:
                header = f"{proj.name} ({proj.tech_used})" if proj.name else proj.tech_used
            if header:
                lines.append(f"### {header}")
            if proj.bullets:
                for bullet in proj.bullets:
                    b = bullet.strip()
                    if b:
                        lines.append(b if b.startswith("-") else f"- {b}")
            elif proj.description:
                desc = proj.description.strip()
                if desc:
                    lines.append(f"- {desc}")

    if cv.education:
        lines += ["", "## Education"]
        for edu in cv.education:
            lines.append("")
            parts = [edu.degree, edu.university, edu.year]
            if edu.gpa:
                parts.append(f"GPA {edu.gpa}")
            lines.append(" — ".join(p for p in parts if p))

    if cv.certifications:
        lines += ["", "## Certifications"]
        for cert in cv.certifications:
            if cert.strip():
                lines.append(f"- {cert.strip()}")

    if cv.languages:
        lines += ["", "## Languages", ", ".join(cv.languages)]

    return "\n".join(lines).strip()


def _format_skills_section(cv: CVData) -> List[str]:
    if cv.skills_by_category:
        lines = ["## Technical Skills"]
        for key, label in _SKILL_LABELS.items():
            items = cv.skills_by_category.get(key) or []
            if items:
                lines.append(f"**{label}:** {', '.join(items)}")
        return lines
    if cv.skills:
        return ["## Technical Skills", ", ".join(cv.skills)]
    return []


def _format_experience_block(exp: Experience) -> List[str]:
    block: List[str] = [""]
    header_parts = [exp.job_title, exp.company, exp.location]
    dates = " — ".join(p for p in [exp.start_date, exp.end_date] if p)
    if dates:
        header_parts.append(dates)
    header = " · ".join(p for p in header_parts if p)
    block.append(f"### {header}" if header else "### Role")
    for bullet in exp.bullets:
        b = bullet.strip()
        if b:
            block.append(b if b.startswith("-") else f"- {b}")
    return block
