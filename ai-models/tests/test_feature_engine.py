"""Tests for layer 4 — CV feature / facts engine."""

from cv_analysis.features.feature_engine import build_cv_facts
from cv_analysis.parsing.structured_cv import extract_structured_cv

SAMPLE_CV = """
Alex Chen
alex@example.com | +1 555 0100

## Summary
Junior developer with React experience.

## Experience
### Acme Corp — Intern
- Built React components used by 500+ users
- Reduced page load time by 20%

## Projects
Todo app in React.

## Skills
React, JavaScript, TypeScript

## Education
BSc Computer Science, 2024
""".strip()


def test_build_cv_facts_word_and_bullet_counts():
    structured = extract_structured_cv(SAMPLE_CV)
    facts = build_cv_facts(structured)
    assert facts.word_count >= 30
    assert facts.bullet_count >= 2
    assert facts.metrics_count >= 1


def test_build_cv_facts_sections_and_contact():
    structured = extract_structured_cv(SAMPLE_CV)
    facts = build_cv_facts(structured)
    assert "summary" in facts.sections_present
    assert "experience" in facts.sections_present
    assert facts.has_contact is True
    assert facts.experience_roles >= 1
    assert facts.skills_count >= 2
