"""Regression tests for Full_Stack_Developer_CV_Sample.pdf parsing + scoring."""

from pathlib import Path

import pytest

from cv_analysis.features.feature_engine import build_cv_facts
from cv_analysis.parsing.structured_cv import extract_structured_cv
from cv_analysis.parsing.text_pipeline import parse_cv_file_for_analysis, slice_section

SAMPLE_PDF = Path("/home/basmalaalaa/Downloads/Full_Stack_Developer_CV_Sample.pdf")


@pytest.mark.skipif(not SAMPLE_PDF.is_file(), reason="Sample PDF not on disk")
def test_full_stack_sample_extracts_all_sections():
    prepared = parse_cv_file_for_analysis(SAMPLE_PDF.read_bytes(), SAMPLE_PDF.name)
    lower = prepared.lower()
    for section in (
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "languages",
    ):
        assert section in lower, f"missing section: {section}"


@pytest.mark.skipif(not SAMPLE_PDF.is_file(), reason="Sample PDF not on disk")
def test_full_stack_sample_not_flagged_too_brief():
    prepared = parse_cv_file_for_analysis(SAMPLE_PDF.read_bytes(), SAMPLE_PDF.name)
    structured = extract_structured_cv(prepared)
    facts = build_cv_facts(structured)
    assert facts.word_count >= 200


@pytest.mark.skipif(not SAMPLE_PDF.is_file(), reason="Sample PDF not on disk")
def test_full_stack_sample_sections_detected_in_facts():
    prepared = parse_cv_file_for_analysis(SAMPLE_PDF.read_bytes(), SAMPLE_PDF.name)
    structured = extract_structured_cv(prepared)
    facts = build_cv_facts(structured)
    for section in ("summary", "skills", "experience", "projects", "education"):
        assert section in facts.sections_present, f"missing from facts: {section}"
    assert facts.word_count >= 200
    assert facts.bullet_count >= 4


@pytest.mark.skipif(not SAMPLE_PDF.is_file(), reason="Sample PDF not on disk")
def test_full_stack_sample_experience_has_bullets():
    prepared = parse_cv_file_for_analysis(SAMPLE_PDF.read_bytes(), SAMPLE_PDF.name)
    exp = slice_section(prepared, "experience", "work history", "employment")
    assert exp.count("\n- ") >= 4 or exp.count("\n-") >= 4
