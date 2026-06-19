"""Tests for PDF → section detection → analysis text pipeline."""

from cv_analysis.parsing.text_pipeline import (
    inject_section_breaks,
    prepare_cv_for_analysis,
    slice_section,
    structure_cv_text,
)
from cv_analysis.features.feature_engine import build_cv_facts
from cv_analysis.parsing.structured_cv import extract_cv_metadata, extract_structured_cv


FLAT_PDF_CV = """
Basmala Alaa
basmala@example.com | +20 100 000 0000 | linkedin.com/in/basmala

PROFESSIONAL SUMMARY
Full stack developer with 4 years building React and Node.js applications.
Delivered production systems for fintech and e-commerce clients.

SKILLS
React, TypeScript, Node.js, Python, PostgreSQL, Docker, AWS, Git

EXPERIENCE
Full Stack Developer | TechCorp | Cairo | 2021 – Present
• Built REST APIs serving 50k daily users with Node.js and PostgreSQL
• Led migration of legacy jQuery app to React, cutting load time by 40%
• Implemented CI/CD pipelines with GitHub Actions and Docker

Junior Developer | StartupHub | 2019 – 2021
• Developed customer dashboard using React and Redux
• Integrated payment gateway reducing checkout errors by 15%

EDUCATION
BSc Computer Science, Cairo University, 2019
""".strip()


def test_inject_section_breaks_splits_embedded_headers():
    blob = "PROFESSIONAL SUMMARY Experienced engineer SKILLS Python, React"
    out = inject_section_breaks(blob)
    assert "## Professional Summary" in out
    assert "## Skills" in out


def test_structure_cv_text_adds_markdown_sections():
    structured = structure_cv_text(FLAT_PDF_CV)
    assert structured.startswith("# Basmala Alaa")
    assert "## Professional Summary" in structured
    assert "## Skills" in structured
    assert "## Experience" in structured
    assert "## Education" in structured
    assert structured.count("- Built REST") >= 1 or "Built REST" in structured


def test_prepare_cv_for_analysis_preserves_editor_markdown():
    md = "## Professional Summary\nHello\n\n## Skills\nPython"
    assert prepare_cv_for_analysis(md, filename="cv.txt") == md


def test_slice_section_finds_pdf_style_headings():
    structured = prepare_cv_for_analysis(FLAT_PDF_CV, filename="resume.pdf")
    summary = slice_section(structured, "summary", "profile")
    skills = slice_section(structured, "skills")
    assert "Full stack developer" in summary
    assert "React" in skills


def test_extract_metadata_from_structured_pdf_text():
    structured = prepare_cv_for_analysis(FLAT_PDF_CV, filename="resume.pdf")
    meta = extract_cv_metadata(structured)
    assert "Full Stack" in meta["target_role"] or "Developer" in meta["target_role"]
    assert "React" in meta["job_description"]
    assert meta["job_description"]


def test_facts_detect_sections_after_pipeline():
    structured = prepare_cv_for_analysis(FLAT_PDF_CV, filename="resume.pdf")
    cv = extract_structured_cv(structured)
    facts = build_cv_facts(cv)
    assert "summary" in facts.sections_present or "experience" in facts.sections_present
    assert facts.word_count >= 50
    assert facts.bullet_count >= 2
