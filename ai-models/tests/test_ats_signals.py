"""Tests for deterministic ATS signals fed to the ATS judge."""

from cv_analysis.features.ats_signals import build_ats_signals
from cv_analysis.judges.schemas import CvFacts, CvSection, StructuredCv


def _structured(**kwargs) -> StructuredCv:
    defaults = dict(
        raw_markdown="",
        header={},
        sections={},
        target_role="Full Stack Developer",
        company="",
    )
    defaults.update(kwargs)
    return StructuredCv(**defaults)


def test_ats_signals_flags_pdf_source():
    structured = _structured()
    facts = CvFacts()
    out = build_ats_signals(structured, facts, filename="resume.pdf", target_role="Full Stack Developer")
    assert "PDF" in out
    assert ".docx" in out


def test_ats_signals_detects_bullets_in_experience():
    structured = _structured(
        raw_markdown="## Experience\n### Dev\n- Built APIs\n- Led team",
        sections={"experience": CvSection(name="Experience", body="- Built APIs\n- Led team")},
    )
    facts = CvFacts(bullet_count=2)
    out = build_ats_signals(structured, facts, filename="cv.docx")
    assert "bullet" in out.lower()


def test_ats_signals_role_keywords_in_summary_and_skills():
    structured = _structured(
        raw_markdown="## Summary\nFull stack developer\n## Skills\nReact, Node.js",
        sections={
            "summary": CvSection(name="Summary", body="Full stack developer"),
            "skills": CvSection(name="Skills", body="React, Node.js"),
        },
    )
    facts = CvFacts()
    out = build_ats_signals(structured, facts, target_role="Full Stack Developer")
    assert "summary" in out.lower() or "skills" in out.lower()


def test_ats_signals_reports_links():
    structured = _structured(
        raw_markdown="github.com/jane",
        header={"links": "github.com/jane | linkedin.com/in/jane"},
    )
    facts = CvFacts(has_links=True)
    out = build_ats_signals(structured, facts)
    assert "github.com" in out.lower() or "plain text" in out.lower()


def test_ats_signals_includes_missing_jd_keywords():
    structured = _structured()
    facts = CvFacts()
    out = build_ats_signals(
        structured, facts, missing_keywords=["React", "Kubernetes"],
    )
    assert "React" in out
    assert "Kubernetes" in out
    assert "not found" in out.lower()
