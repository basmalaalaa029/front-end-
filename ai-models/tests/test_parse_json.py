"""Tests for parse_json_robust helper."""

from cv_agent.app.utils import parse_json_robust


def test_parse_json_robust_salvages_truncated_judge_scores():
    raw = (
        '{"clarity_score": 72, "structure_score": 68, "impact_score": 55, '
        '"skills_relevance_score": 60, "ats_readiness_score": 70, '
        '"overall_score": 65, "strengths": ["Good structure"], '
        '"weaknesses": ["Needs more metrics", "Summary is weak"], '
        '"improvement_suggestions": ["Add numbers", "Rewrite summary"], '
        '"rewrite_suggestions": ["Increased revenue by 20%'
    )
    data = parse_json_robust(raw)
    assert data["clarity_score"] == 72
    assert data["overall_score"] == 65
    assert len(data.get("weaknesses", [])) >= 2


def test_parse_json_robust_parses_valid_json():
    raw = '{"clarity_score": 80, "overall_score": 80}'
    data = parse_json_robust(raw)
    assert data["clarity_score"] == 80
