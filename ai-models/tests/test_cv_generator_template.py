"""Tests for cv_generator template fill and markdown conversion."""

from cv_generator.models.cv_schema import CVData, Education, Experience, Project
from cv_generator.services.template_service import fill_template
from cv_generator.markdown import cv_data_to_markdown


def _sample_cv() -> CVData:
    return CVData(
        full_name="Jane Doe",
        target_role="Full Stack Developer",
        email="jane@example.com",
        phone="+1 555 0100",
        summary="Developer with React and Node experience.",
        skills=["React", "Node.js", "PostgreSQL"],
        experience=[
            Experience(
                job_title="Software Engineer",
                company="Acme Corp",
                start_date="2021",
                end_date="2024",
                bullets=["Built APIs serving 500 users"],
            ),
        ],
        projects=[
            Project(name="Portfolio", tech_used="React", description="Personal site"),
        ],
        education=[
            Education(degree="BSc CS", university="State University", year="2021"),
        ],
    )


def test_fill_template_returns_markdown():
    result = fill_template(_sample_cv())
    assert result["status"] == "success"
    assert result["version"] == "template"
    assert "## Professional Summary" in result["markdown"]
    assert "Software Engineer" in result["markdown"]
    assert "jane@example.com" not in result["markdown"]


def test_cv_data_to_markdown_includes_sections():
    md = cv_data_to_markdown(_sample_cv())
    assert "## Professional Summary" in md
    assert "## Work Experience" in md
    assert "## Projects" in md
    assert "## Education" in md
    assert "## Technical Skills" in md
    assert "# Jane Doe" not in md


def test_cv_data_to_markdown_categorized_skills():
    cv = _sample_cv()
    cv.skills_by_category = {
        "frontend": ["React"],
        "backend": ["Node.js"],
        "databases": ["PostgreSQL"],
    }
    md = cv_data_to_markdown(cv)
    assert "**Frontend:** React" in md
    assert "**Backend:** Node.js" in md


def test_cv_data_to_markdown_project_description_as_single_bullet():
    cv = _sample_cv()
    md = cv_data_to_markdown(cv)
    assert "- Personal site" in md


def test_to_generation_input_does_not_duplicate_project_description():
    cv = _sample_cv()
    payload = cv.to_generation_input()
    project = payload["projects"][0]
    assert project["description"] == "Personal site"
    assert project["bullets"] == []
