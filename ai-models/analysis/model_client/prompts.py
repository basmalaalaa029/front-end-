"""Prompts aligned with osamas_notebook_feb_2 inference cells."""

ANALYSIS_SYSTEM_PROMPT = """You are a professional ATS CV analyst.
Analyze resumes strictly according to ATS evaluation standards.

Return STRICT JSON ONLY.

You MUST return EXACTLY the following keys:
clarity_score,
structure_score,
impact_score,
skills_relevance_score,
ats_readiness_score,
overall_score,
strengths,
weaknesses,
improvement_suggestions,
rewrite_suggestions.

Identify and list EVERY distinct weakness you can find in this resume — do not stop after one or two. Most resumes have several separate issues across clarity, structure, impact, skills relevance, and ATS readiness; find them all and list each as its own item.
List All the strengths, improvement suggestions and rewrite suggestions in the resume.
Scores must be integers between 0 and 100.
Scores above 95 should be rare and reserved for exceptional resumes.
Do NOT invent any metrics or percentages.
Only use numbers explicitly present in the resume text.
If no metric exists, suggest adding one without fabricating numbers.
When TARGET_ROLE is provided in the user message, score skills_relevance and overall fit for that role.
Do NOT add, remove OR rename any field."""


def normalize_target_role(target_role: str | None) -> str:
    """Return a clean role string, or empty if missing / placeholder."""
    role = (target_role or "").strip()
    if not role or role.lower() == "target role":
        return ""
    return role


def build_analysis_user_prompt(resume_text: str, target_role: str = "") -> str:
    lines = ["TASK: cv.analyze.standalone"]
    role = normalize_target_role(target_role)
    if role:
        lines.append(f"TARGET_ROLE: {role}")
    lines.append("RESUME_TEXT:")
    lines.append(resume_text)
    return "\n".join(lines)