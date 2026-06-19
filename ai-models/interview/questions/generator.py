"""Interview question generation from CV context."""

from __future__ import annotations

import re
import uuid
from typing import List

from interview.api.schemas import InterviewQuestion


def generate_questions(cv_text: str, target_role: str, company: str) -> List[InterviewQuestion]:
    company_bit = f" at {company}" if company.strip() else ""
    role = target_role.strip() or "this role"

    base = [
        (
            "behavioral",
            f"Walk me through a project from your CV that best demonstrates your fit for {role}{company_bit}.",
        ),
        (
            "technical",
            "What technical challenges did you face in your most recent role, and how did you solve them?",
        ),
        (
            "impact",
            "Describe a time you delivered measurable impact — include numbers if possible.",
        ),
        (
            "collaboration",
            "Tell me about a situation where you had to push back on a stakeholder or PM. What was the outcome?",
        ),
        (
            "growth",
            f"Why are you interested in {role}{company_bit}, and what would you bring in your first 90 days?",
        ),
    ]

    skills = _extract_skills(cv_text)
    if skills:
        base.insert(
            2,
            ("skills", f"How have you applied {skills[0]} in production? Give a concrete example."),
        )

    return [
        InterviewQuestion(id=str(uuid.uuid4())[:8], text=text, category=cat)
        for cat, text in base[:5]
    ]


def _extract_skills(cv_text: str) -> List[str]:
    common = [
        "react", "python", "typescript", "javascript", "node", "aws", "docker",
        "kubernetes", "sql", "java", "figma", "design systems",
    ]
    lower = cv_text.lower()
    return [s.title() if s != "aws" else "AWS" for s in common if s in lower][:3]
