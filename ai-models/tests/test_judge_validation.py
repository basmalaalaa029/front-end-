"""Tests for generic judge validation and CV inventory (any CV, not hardcoded cases)."""

from cv_analysis.features.cv_inventory import build_cv_inventory, full_cv_text_for_judge
from cv_analysis.judges.judge_validation import (
    audit_judge_output_quality,
    is_near_duplicate,
    text_overlap_ratio,
    triple_has_quality_issues,
    validate_judge_output,
    weakness_contradicts_cv,
)
from cv_analysis.judges.schemas import CvFacts, CvSection, JudgeOutput, StructuredCv


def _structured(cv_text: str, **sections: str) -> StructuredCv:
    return StructuredCv(
        raw_markdown=cv_text,
        sections={k: CvSection(name=k.title(), body=v) for k, v in sections.items()},
        target_role="Developer",
    )


def test_inventory_lists_roles_skills_and_education_years():
    cv = (
        "## Experience\n"
        "### Full Stack Developer\n"
        "Tech Co (2023 – Present)\n"
        "- Built APIs for 15,000+ users\n"
        "## Skills\n"
        "PostgreSQL, React, Node.js\n"
        "## Education\n"
        "BSc Computer Science, Cairo University (2021)"
    )
    facts = CvFacts(
        sections_present=["experience", "skills", "education"],
        metrics_count=1,
        has_contact=True,
        bullet_count=1,
    )
    structured = _structured(
        cv,
        experience="### Full Stack Developer\nTech Co (2023 – Present)\n- Built APIs for 15,000+ users",
        skills="PostgreSQL, React, Node.js",
        education="BSc Computer Science, Cairo University (2021)",
    )
    inv = build_cv_inventory(structured, facts)
    assert "PostgreSQL" in inv
    assert "Full Stack Developer" in inv
    assert "2021" in inv
    assert "15,000" in inv or "15000" in inv.lower() or "users" in inv


def test_full_cv_text_not_truncated_for_short_cv():
    cv = "x" * 2000
    structured = StructuredCv(raw_markdown=cv)
    assert len(full_cv_text_for_judge(structured)) == 2000


def test_overlap_detects_example_already_in_cv():
    cv_lower = (
        "full stack developer with 3 years building web applications using "
        "react node.js rest apis and sql databases"
    )
    rewrite = (
        "Full Stack Developer with 3+ years of experience building web applications "
        "using React, Node.js, REST APIs, and SQL databases."
    )
    assert text_overlap_ratio(rewrite, cv_lower) >= 0.72


def test_validate_drops_issue_when_rewrite_matches_cv():
    cv = (
        "Summary: Full Stack Developer with 3+ years building web applications "
        "using React, Node.js, REST APIs, and SQL databases."
    )
    scores = JudgeOutput(
        weaknesses=["The summary could be more specific."],
        improvement_suggestions=["Add React and Node.js to the summary."],
        rewrite_suggestions=[
            "Full Stack Developer with 3+ years building web applications using "
            "React, Node.js, REST APIs, and SQL databases."
        ],
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    # Presentation-quality issues are kept even when rewrite overlaps CV.
    assert len(cleaned.weaknesses) == 1


def test_validate_drops_postgresql_false_positive():
    cv = (
        "## Skills\nPostgreSQL, React, Node.js, Docker\n"
        "## Experience\n### Full Stack Developer\n- Built APIs with PostgreSQL"
    )
    facts = CvFacts(sections_present=["skills", "experience"], bullet_count=1)
    structured = _structured(
        cv,
        skills="PostgreSQL, React, Node.js, Docker",
        experience="### Full Stack Developer\n- Built APIs with PostgreSQL",
    )
    scores = JudgeOutput(
        weaknesses=["No mention of specific databases like PostgreSQL in skills"],
        improvement_suggestions=["Include PostgreSQL under databases in the skills section"],
        rewrite_suggestions=["Databases: PostgreSQL, MySQL"],
    )
    cleaned = validate_judge_output(
        scores, cv_text=cv, structured=structured, facts=facts,
    )
    assert cleaned.weaknesses == []


def test_validate_drops_missing_job_title_false_positive():
    cv = (
        "## Experience\n"
        "### Full Stack Developer\n"
        "Tech Solutions Egypt (Jan 2023 – Present)\n"
        "- Built web applications"
    )
    facts = CvFacts(sections_present=["experience"], bullet_count=1)
    structured = _structured(
        cv,
        experience=(
            "### Full Stack Developer\n"
            "Tech Solutions Egypt (Jan 2023 – Present)\n"
            "- Built web applications"
        ),
    )
    scores = JudgeOutput(
        weaknesses=["Some missing job title in experience section"],
        improvement_suggestions=["Add 'Full Stack Developer' as the job title in the experience section"],
        rewrite_suggestions=[
            "Developed and maintained web applications as a Full Stack Developer at Tech Solutions Egypt."
        ],
    )
    cleaned = validate_judge_output(
        scores, cv_text=cv, structured=structured, facts=facts,
    )
    assert cleaned.weaknesses == []


def test_validate_keeps_presentation_weak_metrics():
    cv = "## Experience\n- Worked on backend services for the team"
    scores = JudgeOutput(
        weaknesses=["Experience bullets are vague and lack measurable impact."],
        improvement_suggestions=["Add numbers such as users served or latency reduced."],
        rewrite_suggestions=["Built backend APIs serving 5,000+ daily users, reducing latency by 30%."],
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert len(cleaned.weaknesses) == 1


def test_validate_dedupes_semantic_duplicates():
    scores = JudgeOutput(
        weaknesses=[
            "No mention of PostgreSQL in skills section",
            "Skills section lacks database specifics like PostgreSQL",
        ],
        improvement_suggestions=["Add PostgreSQL", "List PostgreSQL under databases"],
        rewrite_suggestions=["Skills: PostgreSQL", "PostgreSQL, MySQL"],
    )
    cv = "## Skills\nPython only"
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert len(cleaned.weaknesses) == 1


def test_validate_drops_absence_claim_when_suggestion_already_in_cv():
    cv = "Education: Bachelor of Computer Science, Cairo University (2021), GPA 3.4"
    scores = JudgeOutput(
        weaknesses=["Education section does not include a graduation date."],
        improvement_suggestions=["Add graduation year 2021 to education."],
        rewrite_suggestions=["Bachelor of Computer Science, Cairo University (2021), GPA 3.4"],
    )
    assert weakness_contradicts_cv(
        scores.weaknesses[0],
        scores.improvement_suggestions[0],
        scores.rewrite_suggestions[0],
        cv.lower(),
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert cleaned.weaknesses == []


def test_validate_keeps_genuine_gap():
    cv = "## Skills\nPython, JavaScript"
    scores = JudgeOutput(
        weaknesses=["No tailored cover letter for this employer."],
        improvement_suggestions=["Write a short paragraph explaining interest in this company."],
        rewrite_suggestions=["I am excited to apply because your mission aligns with my values."],
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert len(cleaned.weaknesses) == 1


def test_validate_drops_copy_paste_triple():
    cv = "## Skills\nPython"
    scores = JudgeOutput(
        weaknesses=["Skills section lacks specific database tools."],
        improvement_suggestions=["Skills section lacks specific database tools."],
        rewrite_suggestions=["Skills section lacks specific database tools."],
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert cleaned.weaknesses == []


def test_validate_drops_generic_rewrite():
    cv = "## Experience\nWorked on backend services"
    scores = JudgeOutput(
        weaknesses=["Experience bullets lack measurable outcomes."],
        improvement_suggestions=["Add user counts or latency improvements to each role."],
        rewrite_suggestions=["Consider converting bullets to include specific metrics."],
    )
    cleaned = validate_judge_output(scores, cv_text=cv)
    assert cleaned.weaknesses == []


def test_audit_judge_output_quality_combined():
    data = {
        "ats": {
            "weaknesses": ["Issue one"],
            "improvement_suggestions": ["Issue one"],
            "rewrite_suggestions": ["Add role keywords to the summary."],
        },
        "hr": {
            "weaknesses": ["Issue A", "Issue B"],
            "improvement_suggestions": ["Fix A"],
            "rewrite_suggestions": ["Fix A", "Example B"],
        },
    }
    errors = audit_judge_output_quality(data)
    assert any("ats[0]" in e for e in errors)
    assert any("hr:" in e and "mismatch" in e for e in errors)


def test_triple_has_quality_issues_detects_verbatim_copy():
    assert triple_has_quality_issues(
        "Summary is too vague.",
        "Summary is too vague.",
        "Write a stronger summary.",
    )
