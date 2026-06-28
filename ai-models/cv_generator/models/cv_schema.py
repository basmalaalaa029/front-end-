"""Structured CV data models for template fill and Gemini enhancement."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Experience(BaseModel):
    job_title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str = ""
    tech_used: str = ""
    description: str = ""
    bullets: List[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str = ""
    university: str = ""
    year: str = ""
    gpa: Optional[str] = None


class EducationInput(BaseModel):
    degree: str
    university: str
    year: str
    gpa: Optional[str] = None


class ExperienceInput(BaseModel):
    job_title: str
    company: str
    start_date: str
    end_date: str
    description: str = ""


class ProjectInput(BaseModel):
    name: str = ""
    tech_used: str = ""
    description: str = ""


class WizardStep1Request(BaseModel):
    """Wizard step 1 — structured basics before AI generation."""

    full_name: str
    target_job: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    education: List[EducationInput]
    experience: List[ExperienceInput] = Field(default_factory=list)
    has_experience: bool = True
    projects: List[ProjectInput] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    def to_cv_data(self) -> "CVData":
        """Map wizard form data into CVData for template fill / Gemini."""
        experience: List[Experience] = []
        if self.has_experience:
            for exp in self.experience:
                desc = (exp.description or "").strip()
                bullets: List[str] = []
                if desc:
                    lines = [ln.strip() for ln in desc.splitlines() if ln.strip()]
                    bullets = lines if lines else [desc]
                experience.append(
                    Experience(
                        job_title=exp.job_title.strip(),
                        company=exp.company.strip(),
                        start_date=exp.start_date.strip(),
                        end_date=exp.end_date.strip(),
                        bullets=bullets,
                    ),
                )

        education = [
            Education(
                degree=e.degree.strip(),
                university=e.university.strip(),
                year=e.year.strip(),
                gpa=(e.gpa or "").strip() or None,
            )
            for e in self.education
            if e.degree.strip() or e.university.strip()
        ]

        projects: List[Project] = []
        for proj in self.projects:
            name = proj.name.strip()
            tech = proj.tech_used.strip()
            desc = proj.description.strip()
            if not name and not desc:
                continue
            bullets: List[str] = []
            if desc:
                lines = [ln.strip() for ln in desc.splitlines() if ln.strip()]
                bullets = lines if lines else [desc]
            projects.append(
                Project(
                    name=name,
                    tech_used=tech,
                    description=desc if not bullets else "",
                    bullets=bullets,
                ),
            )

        certifications = [c.strip() for c in self.certifications if c and c.strip()]

        return CVData(
            full_name=self.full_name.strip(),
            target_role=self.target_job.strip(),
            email=(self.email or "").strip(),
            phone=(self.phone or "").strip(),
            location=(self.location or "").strip() or None,
            linkedin=(self.linkedin or "").strip() or None,
            github=(self.github or "").strip() or None,
            skills=[],
            experience=experience,
            projects=projects,
            education=education,
            certifications=certifications or None,
            has_experience=self.has_experience,
        )


class CVData(BaseModel):
    full_name: str = ""
    target_role: str = ""
    email: str = ""
    phone: str = ""
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    skills_by_category: Optional[Dict[str, List[str]]] = None
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    has_experience: bool = True

    def is_complete(self) -> bool:
        has_content = bool(self.experience) or bool(self.projects)
        return bool(self.full_name and self.target_role and has_content)

    def to_generation_input(self) -> dict:
        """Build the user payload sent to Gemini for CV generation."""
        return {
            "target_job": self.target_role,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location or "",
            "linkedin": self.linkedin or "",
            "github": self.github or "",
            "portfolio": "",
            "has_experience": self.has_experience,
            "education": [e.model_dump() for e in self.education],
            "experience": [e.model_dump() for e in self.experience],
            "skills": list(self.skills),
            "skills_by_category": dict(self.skills_by_category or {}),
            "projects": [
                {
                    "name": p.name,
                    "tech_used": p.tech_used,
                    "description": p.description if not p.bullets else "",
                    "bullets": list(p.bullets),
                }
                for p in self.projects
            ],
            "certifications": list(self.certifications or []),
            "languages": list(self.languages or []),
            "summary_notes": self.summary,
        }

    @classmethod
    def from_generate_request(cls, req: Any) -> "CVData":
        """Map HTTP GenerateRequest (structured or legacy flat) to CVData."""
        if getattr(req, "experience", None):
            experience = [
                Experience(**e.model_dump()) if hasattr(e, "model_dump") else Experience(**e)
                for e in req.experience
            ]
        else:
            experience = _parse_legacy_experiences(getattr(req, "experiences", None) or [])

        if getattr(req, "projects", None):
            projects = [
                Project(**p.model_dump()) if hasattr(p, "model_dump") else Project(**p)
                for p in req.projects
            ]
        else:
            projects = []

        if getattr(req, "education_structured", None):
            education = [
                Education(**e.model_dump()) if hasattr(e, "model_dump") else Education(**e)
                for e in req.education_structured
            ]
        else:
            education = _parse_legacy_education(getattr(req, "education", None) or [])

        github = getattr(req, "github", None) or ""
        linkedin = req.linkedin or ""
        url = getattr(req, "url", None) or ""
        if url and not github and "github" in url.lower():
            github = url

        return cls(
            full_name=req.full_name,
            target_role=req.target_role,
            email=req.email or "",
            phone=req.phone or "",
            location=getattr(req, "location", None) or getattr(req, "address", None) or "",
            linkedin=linkedin or None,
            github=github or None,
            summary=req.summary or "",
            skills=list(req.skills or []),
            experience=experience,
            projects=projects,
            education=education,
            certifications=list(req.certifications or []) or None,
            languages=getattr(req, "languages", None),
        )

    @model_validator(mode="after")
    def _normalize_lists(self) -> "CVData":
        self.skills = [s.strip() for s in self.skills if s and s.strip()]
        return self

    def to_generated_cv_json(self) -> dict:
        """Map merged CVData to the wizard API / frontend GeneratedCv shape."""
        if self.skills_by_category:
            skills_field: Any = dict(self.skills_by_category)
        elif self.skills:
            skills_field = list(self.skills)
        else:
            skills_field = {}

        return {
            "personal_info": {
                "full_name": self.full_name,
                "email": self.email,
                "phone": self.phone,
                "location": self.location or "",
                "linkedin": self.linkedin or "",
                "github": self.github or "",
                "portfolio": "",
            },
            "target_title": self.target_role,
            "summary": self.summary,
            "skills": skills_field,
            "experience": [
                {
                    "job_title": e.job_title,
                    "company": e.company,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "bullets": list(e.bullets),
                }
                for e in self.experience
            ],
            "projects": [
                {
                    "name": p.name,
                    "tech_used": p.tech_used,
                    "description": p.description,
                    "bullets": list(p.bullets),
                }
                for p in self.projects
            ],
            "education": [
                {
                    "degree": e.degree,
                    "university": e.university,
                    "year": e.year,
                    "gpa": e.gpa,
                }
                for e in self.education
            ],
            "certifications": list(self.certifications or []),
            "languages": list(self.languages or []),
        }


def _parse_legacy_experiences(flat: List[str]) -> List[Experience]:
    """Parse flattened experience blocks from legacy API payloads."""
    out: List[Experience] = []
    for block in flat:
        block = (block or "").strip()
        if not block:
            continue
        lines = block.splitlines()
        header = lines[0].strip()
        parts = [p.strip() for p in header.split("·")]
        job_title = parts[0] if parts else header
        company = parts[1] if len(parts) > 1 else ""
        location = parts[2] if len(parts) > 2 else ""
        dates = parts[3] if len(parts) > 3 else ""
        start_date, end_date = _split_dates(dates)
        bullets = []
        for line in lines[1:]:
            line = line.strip().lstrip("-").strip()
            if line:
                bullets.append(line)
        if header.lower().startswith("project"):
            continue
        out.append(Experience(
            job_title=job_title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            bullets=bullets,
        ))
    return out


def _parse_legacy_education(flat: List[str]) -> List[Education]:
    out: List[Education] = []
    for line in flat:
        line = (line or "").strip()
        if not line:
            continue
        gpa = None
        gpa_m = re.search(r"GPA\s+([\d.]+)", line, re.I)
        if gpa_m:
            gpa = gpa_m.group(1)
            line = re.sub(r"\s*GPA\s+[\d.]+\s*", "", line, flags=re.I).strip(" —")
        parts = [p.strip() for p in line.split("—")]
        university = parts[0] if parts else line
        degree = parts[1] if len(parts) > 1 else ""
        year = parts[2] if len(parts) > 2 else ""
        out.append(Education(degree=degree, university=university, year=year, gpa=gpa))
    return out


def _split_dates(dates: str) -> tuple[str, str]:
    if not dates:
        return "", ""
    for sep in ("—", "-", "–", " to "):
        if sep in dates:
            a, b = dates.split(sep, 1)
            return a.strip(), b.strip()
    return dates.strip(), ""
