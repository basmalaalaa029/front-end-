"""Tests for robust judge JSON parsing and truncated-output salvage."""

from cv_analysis.judges.schemas import JudgeOutput
from cv_analysis.judges.utils import parse_json_robust


def test_parse_json_robust_salvages_truncated_judge_scores():
    raw = """```json
{
  "clarity_score": 85,
  "structure_score": 80,
  "impact_score": 75,
  "skills_relevance_score": 70,
  "ats_r"""
    data = parse_json_robust(raw)
    assert data
    assert data["clarity_score"] == 85
    assert data["structure_score"] == 80
    assert data["impact_score"] == 75
    assert data["skills_relevance_score"] == 70
    assert "overall_score" in data


def test_parse_json_robust_salvages_complete_weakness_strings():
    raw = """
{
  "clarity_score": 60,
  "structure_score": 55,
  "impact_score": 40,
  "skills_relevance_score": 50,
  "ats_readiness_score": 45,
  "overall_score": 50,
  "strengths": [],
  "weaknesses": [
    "Skills section uses generic labels instead of specific tools.",
    "Experience bullets lack measurable impact."
  ],
  "improvement_suggestions": [
    "List React, Node.js, and PostgreSQL in Skills.",
    "Add metrics such as users served per role."
  ],
  "rewrite_suggestions": [
    "JavaScript, React, Node.js, PostgreSQL, Git",
    "Built APIs serving 5,000+ users, reducing latency by 25%."
  ],
  "ats_read"""
    data = parse_json_robust(raw)
    assert len(data.get("weaknesses", [])) == 2
    assert len(data.get("improvement_suggestions", [])) == 2
    assert len(data.get("rewrite_suggestions", [])) == 2
    scores = JudgeOutput(**{k: v for k, v in data.items() if k in JudgeOutput.model_fields})
    assert scores.clarity_score == 60
    assert len(scores.weaknesses) == 2
