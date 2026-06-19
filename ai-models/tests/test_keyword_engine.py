"""Tests for layer 5 — keyword matching engine."""

from cv_analysis.keywords.keyword_engine import match_keywords
from cv_analysis.judges.schemas import JDContext

CV_TEXT = """
## Skills
React, JavaScript, HTML, CSS

## Experience
Built frontend features with React.
""".strip()


def test_match_keywords_coverage_and_missing():
    jd = JDContext(
        keywords=["React", "TypeScript", "Docker", "Kubernetes"],
        canonical_skills=["AWS", "CI/CD"],
    )
    result = match_keywords(CV_TEXT, jd)

    names = {row.name.lower() for row in result.coverage}
    assert "react" in names
    assert any(row.name == "React" and row.coverage == 100 for row in result.coverage)

    missing_lower = {k.lower() for k in result.missing_keywords}
    assert "typescript" in missing_lower or "docker" in missing_lower
    assert "react" not in missing_lower


def test_match_keywords_empty_jd():
    result = match_keywords(CV_TEXT, JDContext())
    assert result.coverage == []
    assert result.missing_keywords == []
