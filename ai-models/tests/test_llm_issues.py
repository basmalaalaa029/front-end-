"""Tests for LLM-native issue cards (no static templates)."""

from cv_analysis.judges.judge_validation import is_near_duplicate, validate_judge_output
from cv_analysis.judges.llm_analysis import (
    MAX_UI_ISSUE_ITEMS,
    _blend_judges,
    _build_facts_prompt,
    _merge_judge_issue_pairs,
)
from cv_analysis.judges.schemas import (
    CvFacts,
    JDContext,
    JudgeOutput,
    KeywordMatchResult,
    StructuredCv,
    issues_from_judge,
)
from cv_analysis.config import get_cv_analysis_config


def test_issues_from_judge_uses_model_text_directly():
    scores = JudgeOutput(
        overall_score=52,
        clarity_score=60,
        structure_score=55,
        impact_score=20,
        skills_relevance_score=40,
        ats_readiness_score=45,
        weaknesses=[
            "Your skills section lists generic labels instead of specific technologies.",
            "Experience lines do not include measurable results.",
        ],
        improvement_suggestions=[
            "Replace broad labels with tools you use, such as React, Node.js, and PostgreSQL.",
            "Add two bullets with numbers, for example users served or time saved.",
        ],
        rewrite_suggestions=["Built APIs used by 500+ users using Node.js and PostgreSQL."],
    )
    issues = issues_from_judge(scores)
    assert len(issues) == 2
    assert issues[0].problem == scores.weaknesses[0]
    assert issues[0].recommendation == scores.improvement_suggestions[0]
    assert "generic labels" in issues[0].title.lower() or "skills" in issues[0].title.lower()
    assert issues[0].rewrite == scores.rewrite_suggestions[0]
    assert issues[1].recommendation == scores.improvement_suggestions[1]


def test_issues_from_judge_keeps_index_alignment_when_skipping_parse_failure():
    scores = JudgeOutput(
        overall_score=50,
        weaknesses=[
            "Judge output could not be parsed: timeout",
            "Your summary is too short.",
        ],
        improvement_suggestions=[
            "Re-run analysis.",
            "Write 2–3 sentences about your role and top skills.",
        ],
        rewrite_suggestions=[
            "",
            "Full-stack developer with 3 years building web apps in React and Node.js.",
        ],
    )
    issues = issues_from_judge(scores)
    assert len(issues) == 1
    assert issues[0].problem == "Your summary is too short."
    assert issues[0].recommendation == "Write 2–3 sentences about your role and top skills."
    assert issues[0].rewrite == "Full-stack developer with 3 years building web apps in React and Node.js."


def test_merge_judge_issue_pairs_keeps_suggestion_with_weakness():
    ats = JudgeOutput(
        weaknesses=["Missing contact details", "No bullet points under jobs"],
        improvement_suggestions=["Add email and phone at the top", "Use short bullet lines per role"],
        rewrite_suggestions=["john@email.com | +1 555 0100", "Built a booking app used by 200+ users"],
    )
    hr = JudgeOutput(
        weaknesses=["Missing contact details"],
        improvement_suggestions=["Put your phone number in the header"],
        rewrite_suggestions=["Reach me at john@email.com"],
    )
    w, s, r = _merge_judge_issue_pairs(ats, hr)
    assert w == ["Missing contact details", "No bullet points under jobs"]
    assert s == ["Add email and phone at the top", "Use short bullet lines per role"]
    assert r == ["john@email.com | +1 555 0100", "Built a booking app used by 200+ users"]


def test_blend_judges_does_not_rotate_rewrites():
    cfg = get_cv_analysis_config()
    ats = JudgeOutput(
        overall_score=60,
        weaknesses=["Issue A", "Issue B"],
        improvement_suggestions=["Fix A", "Fix B"],
        rewrite_suggestions=["Example A", "Example B"],
    )
    hr = JudgeOutput(
        overall_score=70,
        weaknesses=["Issue C"],
        improvement_suggestions=["Fix C"],
        rewrite_suggestions=["Example C"],
    )
    blended = _blend_judges(ats, hr, cfg)
    issues = issues_from_judge(blended)
    assert [i.problem for i in issues] == ["Issue A", "Issue B", "Issue C"]
    assert [i.recommendation for i in issues] == ["Fix A", "Fix B", "Fix C"]
    assert [i.rewrite for i in issues] == ["Example A", "Example B", "Example C"]


def test_issues_from_judge_skips_parse_failure_line():
    scores = JudgeOutput.fallback("empty parse result")
    issues = issues_from_judge(scores)
    assert issues == []


def test_judge_fallback_uses_neutral_floor_not_zero():
    scores = JudgeOutput.fallback("timeout")
    assert scores.overall_score == 50
    assert scores.clarity_score == 50
    assert "could not be parsed" in scores.weaknesses[0].lower()


def test_blend_judges_keeps_eight_rewrites_aligned():
    cfg = get_cv_analysis_config()
    n = 8
    ats = JudgeOutput(
        overall_score=60,
        weaknesses=[f"ATS issue {i}" for i in range(n)],
        improvement_suggestions=[f"ATS fix {i}" for i in range(n)],
        rewrite_suggestions=[f"ATS example {i}" for i in range(n)],
    )
    hr = JudgeOutput(overall_score=70, weaknesses=[], improvement_suggestions=[], rewrite_suggestions=[])
    blended = _blend_judges(ats, hr, cfg)
    assert len(blended.weaknesses) == MAX_UI_ISSUE_ITEMS
    assert len(blended.rewrite_suggestions) == len(blended.weaknesses)
    issues = issues_from_judge(blended)
    assert len(issues) == MAX_UI_ISSUE_ITEMS
    for i, issue in enumerate(issues):
        assert issue.rewrite == f"ATS example {i}"


def test_validate_filter_middle_weakness_keeps_pairing():
    cv_text = (
        "Summary: Full stack developer with React and Node.js experience. "
        "Skills: React, Node.js, PostgreSQL. "
        "Experience: Built APIs serving 5000 users."
    )
    scores = JudgeOutput(
        weaknesses=["Issue one", "Missing PostgreSQL in skills", "Issue three"],
        improvement_suggestions=["Fix one", "Add PostgreSQL to skills", "Fix three"],
        rewrite_suggestions=["Example one", "Skills: PostgreSQL, React", "Example three"],
    )
    cleaned = validate_judge_output(scores, cv_text=cv_text)
    issues = issues_from_judge(cleaned)
    assert len(issues) == 2
    assert issues[0].problem == "Issue one"
    assert issues[0].rewrite == "Example one"
    assert issues[1].problem == "Issue three"
    assert issues[1].rewrite == "Example three"


def test_issues_from_judge_uneven_arrays_no_rotation():
    scores = JudgeOutput(
        weaknesses=["Issue A", "Issue B", "Issue C"],
        improvement_suggestions=["Fix A", "Fix B"],
        rewrite_suggestions=["Example A", "Example B"],
    )
    issues = issues_from_judge(scores)
    assert [i.problem for i in issues] == ["Issue A", "Issue B", "Issue C"]
    assert [i.rewrite for i in issues] == ["Example A", "Example B", None]


def test_merge_judge_issue_pairs_semantic_dedup():
    ats = JudgeOutput(
        weaknesses=["No mention of PostgreSQL in skills section"],
        improvement_suggestions=["Add PostgreSQL to skills"],
        rewrite_suggestions=["Skills: PostgreSQL, React"],
    )
    hr = JudgeOutput(
        weaknesses=["Skills section lacks database specifics like PostgreSQL"],
        improvement_suggestions=["List PostgreSQL under databases"],
        rewrite_suggestions=["Databases: PostgreSQL, MySQL"],
    )
    w, s, r = _merge_judge_issue_pairs(ats, hr)
    assert len(w) == 1
    assert is_near_duplicate(w[0], ats.weaknesses[0])


def test_build_facts_prompt_includes_keyword_gaps():
    structured = StructuredCv(raw_markdown="## Skills\nPython")
    facts = CvFacts()
    jd = JDContext(keywords=["React", "Docker", "Python"])
    kw = KeywordMatchResult(
        missing_keywords=["React", "Docker"],
        jd_keywords=["React", "Docker", "Python"],
    )
    prompt = _build_facts_prompt(
        structured, facts, jd, judge_kind="ats", keyword_result=kw,
    )
    assert "KEYWORD GAPS" in prompt
    assert "React" in prompt
    assert "Docker" in prompt
