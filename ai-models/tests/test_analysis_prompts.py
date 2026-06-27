"""Tests for analysis prompt building."""

from analysis.model_client.prompts import build_analysis_user_prompt, normalize_target_role


def test_normalize_target_role_placeholder():
    assert normalize_target_role("") == ""
    assert normalize_target_role("Target role") == ""
    assert normalize_target_role("  target role  ") == ""


def test_build_prompt_without_target_role():
    prompt = build_analysis_user_prompt("John Doe\nEngineer", "")
    assert "TASK: cv.analyze.standalone" in prompt
    assert "TARGET_ROLE" not in prompt
    assert "RESUME_TEXT:" in prompt
    assert "John Doe" in prompt


def test_build_prompt_with_target_role():
    prompt = build_analysis_user_prompt("John Doe\nEngineer", "Full Stack Developer")
    assert "TARGET_ROLE: Full Stack Developer" in prompt
    assert prompt.index("TARGET_ROLE") < prompt.index("RESUME_TEXT")
