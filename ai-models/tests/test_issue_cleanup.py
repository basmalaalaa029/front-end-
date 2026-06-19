"""Tests for lightweight issue cleanup (not full judge validation)."""

from cv_analysis.judges.issue_cleanup import (
    dedupe_strengths,
    filter_missing_keywords_for_prompt,
    prune_judge_output,
    text_overlap_ratio,
)
from cv_analysis.judges.schemas import JudgeOutput


CV = (
    "Full Stack Developer with 3+ years building web applications using "
    "React, Node.js, REST APIs, and SQL databases. Improved latency by 40%."
)


def test_filter_missing_keywords_drops_present_terms():
    missing = filter_missing_keywords_for_prompt(CV, ["React", "Kubernetes", "node.js"])
    assert "React" not in missing
    assert "node.js" not in missing or "Node.js" not in missing
    assert "Kubernetes" in missing


def test_prune_drops_rewrite_already_in_cv():
    scores = JudgeOutput(
        weaknesses=["Summary could be more specific."],
        improvement_suggestions=["Add React and Node.js to the summary."],
        rewrite_suggestions=[
            "Full Stack Developer with 3+ years building web applications using "
            "React, Node.js, REST APIs, and SQL databases."
        ],
    )
    cleaned = prune_judge_output(scores, CV)
    assert cleaned.weaknesses == []


def test_prune_dedupes_near_duplicate_weaknesses():
    scores = JudgeOutput(
        weaknesses=[
            "Experience bullets lack measurable outcomes.",
            "Experience bullets lack measurable outcomes and metrics.",
        ],
        improvement_suggestions=["Add metrics.", "Add metrics to bullets."],
        rewrite_suggestions=["Increased revenue 20%.", "Increased revenue by 20%."],
    )
    cleaned = prune_judge_output(scores, CV)
    assert len(cleaned.weaknesses) == 1


def test_overlap_detects_near_duplicate_cv_text():
    rewrite = (
        "Full Stack Developer with 3+ years of experience building web applications "
        "using React, Node.js, REST APIs, and SQL databases."
    )
    assert text_overlap_ratio(rewrite, CV.lower()) >= 0.72


def test_dedupe_strengths():
    assert dedupe_strengths(["Clear structure", "clear structure", "Strong skills"]) == [
        "Clear structure",
        "Strong skills",
    ]
