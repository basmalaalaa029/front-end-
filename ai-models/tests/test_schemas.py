"""
Tests for Pydantic schema models — JudgeOutput, UserProfile.
"""
import pytest
from cv_generator.models.pipeline import JudgeOutput


class TestJudgeOutput:

    def test_passes_all_above_threshold(self):
        j = JudgeOutput(
            clarity_score=85, structure_score=85, impact_score=85,
            skills_relevance_score=85, ats_readiness_score=85, overall_score=85,
        )
        assert j.passes(82) is True

    def test_passes_fails_one_below(self):
        j = JudgeOutput(
            clarity_score=85, structure_score=85, impact_score=85,
            skills_relevance_score=80, ats_readiness_score=85, overall_score=85,
        )
        assert j.passes(82) is False

    def test_passes_fails_overall_below(self):
        j = JudgeOutput(
            clarity_score=85, structure_score=85, impact_score=85,
            skills_relevance_score=85, ats_readiness_score=85, overall_score=80,
        )
        assert j.passes(82) is False

    def test_lowest_metric(self):
        j = JudgeOutput(
            clarity_score=90, structure_score=50, impact_score=80,
            skills_relevance_score=70, ats_readiness_score=85, overall_score=75,
        )
        assert j.lowest_metric() == "Structure"

    def test_lowest_metric_ats(self):
        j = JudgeOutput(
            clarity_score=90, structure_score=80, impact_score=80,
            skills_relevance_score=70, ats_readiness_score=60, overall_score=75,
        )
        assert j.lowest_metric() == "ATS readiness"

    def test_average_score(self):
        j = JudgeOutput(
            clarity_score=80, structure_score=80, impact_score=80,
            skills_relevance_score=80, ats_readiness_score=80, overall_score=80,
        )
        assert j.average_score() == 80.0

    def test_fallback(self):
        j = JudgeOutput.fallback("test reason")
        assert j.overall_score == 0
        assert "test reason" in j.weaknesses[0]
