"""Tests for cv_generator enhancement validation."""

from cv_generator.models.cv_schema import CVData, Experience
from cv_generator.validation import (
    merge_enhancement,
    normalize_gemini_response,
    validate_enhancement,
    validate_immutable_fields,
    validate_no_invented_metrics,
)


def _base_cv() -> CVData:
    return CVData(
        full_name="Jane Doe",
        target_role="Engineer",
        email="jane@example.com",
        skills=["Python"],
        experience=[
            Experience(
                job_title="Developer",
                company="Acme",
                start_date="2020",
                end_date="2022",
                bullets=["worked on backend services"],
            ),
        ],
    )


def test_merge_preserves_identity_fields():
    original = _base_cv()
    partial = {
        "summary": "Professional engineer.",
        "skills": {
            "backend": ["Python", "FastAPI"],
            "tools": ["Git"],
        },
        "experience": [
            {
                "job_title": "Hacker",
                "company": "Evil Co",
                "start_date": "1999",
                "end_date": "2000",
                "bullets": ["Built REST APIs with FastAPI"],
            },
        ],
    }
    merged = merge_enhancement(original, partial)
    assert merged.experience[0].job_title == "Developer"
    assert merged.experience[0].company == "Acme"
    assert merged.experience[0].bullets[0] == "Built REST APIs with FastAPI"
    assert "Python" in merged.skills
    assert "FastAPI" in merged.skills
    assert merged.skills_by_category == {
        "backend": ["Python", "FastAPI"],
        "tools": ["Git"],
    }


def test_normalize_gemini_response_unwraps_personal_info_and_summary_alias():
    raw = {
        "personal_info": {
            "full_name": "Jane",
            "email": "jane@example.com",
        },
        "professional_summary": "Experienced engineer.",
        "skills": {"backend": ["Python"]},
    }
    normalized = normalize_gemini_response(raw)
    assert normalized["full_name"] == "Jane"
    assert normalized["email"] == "jane@example.com"
    assert normalized["summary"] == "Experienced engineer."


def test_merge_matches_experience_by_identity_not_index():
    original = _base_cv()
    partial = {
        "experience": [
            {
                "job_title": "Other",
                "company": "Elsewhere",
                "start_date": "2018",
                "end_date": "2019",
                "bullets": ["Should not apply"],
            },
            {
                "job_title": "Developer",
                "company": "Acme",
                "start_date": "2020",
                "end_date": "2022",
                "bullets": ["Developed scalable backend services"],
            },
        ],
    }
    merged = merge_enhancement(original, partial)
    assert merged.experience[0].bullets[0] == "Developed scalable backend services"


def test_flatten_categorized_skills():
    from cv_generator.validation import flatten_skills_field

    skills = flatten_skills_field({
        "frontend": ["React.js"],
        "backend": ["Node.js"],
        "databases": ["PostgreSQL"],
    })
    assert skills == ["React.js", "Node.js", "PostgreSQL"]


def test_validate_immutable_fields_detects_title_change():
    original = _base_cv()
    bad = original.model_copy(deep=True)
    bad.experience[0].job_title = "Senior Developer"
    issues = validate_immutable_fields(original, bad)
    assert any("identity" in i for i in issues)


def test_validate_no_invented_metrics():
    original = _base_cv()
    bad = original.model_copy(deep=True)
    bad.experience[0].bullets = ["Improved performance by 40%"]
    issues = validate_no_invented_metrics(original, bad)
    assert any("invented metrics" in i for i in issues)


def test_validate_allows_years_in_summary():
    original = _base_cv()
    good = original.model_copy(deep=True)
    good.summary = "Full Stack Developer with 1 year of experience in backend services."
    assert validate_no_invented_metrics(original, good) == []


def test_validate_enhancement_accepts_good_rewrite():
    original = _base_cv()
    good = original.model_copy(deep=True)
    good.experience[0].bullets = ["Developed backend services for the platform"]
    assert validate_enhancement(original, good) == []
