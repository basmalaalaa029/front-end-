"""Tests for analysis result validation."""

from __future__ import annotations

from analysis.validation.result_validator import AnalysisResult, ResumeIssue, validate_result


SAMPLE_NEW_FORMAT = {
    "clarity_score": 80,
    "structure_score": 75,
    "impact_score": 70,
    "skills_relevance_score": 72,
    "ats_readiness_score": 78,
    "overall_score": 75,
    "strengths": ["Clear experience section", "Strong technical skills"],
    "issues": [
        {
            "issue": "Missing metrics in bullets",
            "whats_wrong": "Experience bullets describe tasks without quantified outcomes.",
            "what_to_do": "Add numbers or scope already present elsewhere in the resume where possible.",
            "example": "Built REST APIs for the payments platform.",
        },
        {
            "issue": "Summary too generic",
            "whats_wrong": "The professional summary does not mention a target role or specialty.",
            "what_to_do": "Tailor the summary to the target role with your strongest relevant skills.",
            "example": "Software engineer with backend and API experience.",
        },
    ],
}

SAMPLE_LEGACY_FORMAT = {
    "clarity_score": 80,
    "structure_score": 75,
    "impact_score": 70,
    "skills_relevance_score": 72,
    "ats_readiness_score": 78,
    "overall_score": 75,
    "strengths": ["Clear experience section"],
    "weaknesses": ["Missing metrics in bullets", "Summary too generic"],
    "improvement_suggestions": [
        "Add quantified outcomes to each experience bullet using numbers already in the resume.",
        "Tailor the summary to the target role with your strongest relevant skills.",
    ],
    "rewrite_suggestions": ["Built REST APIs for payments", "Backend engineer with API experience"],
}


def test_validate_new_structured_issues():
    result, warnings = validate_result(SAMPLE_NEW_FORMAT)
    assert result is not None
    assert len(result.issues) == 2
    assert result.issues[0].issue == "Missing metrics in bullets"
    assert result.issues[0].example.startswith("Built REST")


def test_validate_legacy_flat_arrays_are_zipped():
    result, warnings = validate_result(SAMPLE_LEGACY_FORMAT)
    assert result is not None
    assert len(result.issues) == 2
    assert result.issues[0].whats_wrong == "Missing metrics in bullets"
    assert "quantified outcomes" in result.issues[0].what_to_do
    assert result.issues[0].example == "Built REST APIs for payments"


def test_legacy_preferred_over_structured_issues_without_guidance():
    parsed = {
        **SAMPLE_LEGACY_FORMAT,
        "issues": [
            {
                "issue": "Missing metrics in bullets",
                "whats_wrong": "Missing metrics in bullets",
                "what_to_do": "",
                "example": "",
            }
        ],
    }
    result, _ = validate_result(parsed)
    assert result is not None
    assert result.issues[0].what_to_do
    assert "quantified outcomes" in result.issues[0].what_to_do


def test_issue_dedup_keeps_paired_fields():
    parsed = {
        **SAMPLE_NEW_FORMAT,
        "issues": [
            *SAMPLE_NEW_FORMAT["issues"],
            {
                "issue": "Bullets lack quantitative impact",
                "whats_wrong": "Experience bullets lack metrics and measurable outcomes.",
                "what_to_do": "Quantify results using numbers already in the resume.",
                "example": "Delivered platform improvements for internal users.",
            },
        ],
    }
    result, _ = validate_result(parsed)
    assert result is not None
    assert len(result.issues) <= 3
    for issue in result.issues:
        assert isinstance(issue, ResumeIssue)
        assert issue.whats_wrong
        assert issue.what_to_do


def test_empty_issues_rejected():
    data = {k: v for k, v in SAMPLE_NEW_FORMAT.items() if k != "issues"}
    data["issues"] = []
    result, warnings = validate_result(data)
    assert result is None
    assert warnings


def test_issues_without_what_to_do_rejected():
    data = {
        **SAMPLE_NEW_FORMAT,
        "issues": [
            {
                "issue": "Missing metrics",
                "whats_wrong": "Experience bullets describe tasks without quantified outcomes.",
                "what_to_do": "",
                "example": "",
            }
        ],
    }
    result, warnings = validate_result(data)
    assert result is None


def test_vague_what_to_do_is_dropped():
    data = {
        **SAMPLE_NEW_FORMAT,
        "issues": [
            {
                "issue": "Missing metrics",
                "whats_wrong": "Experience bullets describe tasks without quantified outcomes.",
                "what_to_do": "Update that part of your CV and run analysis again.",
                "example": "",
            }
        ],
    }
    result, _ = validate_result(data)
    assert result is None


def test_analysis_result_model_dump_uses_issues_key():
    result = AnalysisResult.model_validate(SAMPLE_NEW_FORMAT)
    dumped = result.model_dump()
    assert "issues" in dumped
    assert "weaknesses" not in dumped
    assert dumped["issues"][0]["issue"] == "Missing metrics in bullets"
