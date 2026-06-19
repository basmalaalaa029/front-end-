"""Tests for interview feature."""

from interview.api.schemas import StartInterviewRequest, SubmitAnswerRequest
from interview.api.service import (
    evaluate_interview,
    get_session,
    start_interview,
    submit_answer,
)

CV_SAMPLE = """
Jane Smith
Product Designer

## Experience
Led design systems at Square. Shipped 14 features in 2024. Checkout redesign cut drop-off 38%.

## Skills
Figma, design systems, user research, prototyping, React
""".strip()


def test_start_interview_generates_questions():
    resp = start_interview(StartInterviewRequest(cv_text=CV_SAMPLE, target_role="Product Designer"))
    assert resp.session_id
    assert len(resp.questions) >= 3


def test_submit_answer_and_evaluate():
    started = start_interview(StartInterviewRequest(cv_text=CV_SAMPLE, target_role="Product Designer"))
    sid = started.session_id
    q = started.questions[0]

    answer = (
        "At Square I led the checkout redesign. We phased the rollout starting with web, "
        "which cut drop-off by 38% and built the case for mobile."
    )
    sub = submit_answer(sid, SubmitAnswerRequest(question_id=q.id, answer=answer))
    assert sub.score.overall >= 0
    assert sub.score.feedback

    session = get_session(sid)
    assert session.answers_count >= 1

    result = evaluate_interview(sid)
    assert result.overall_score >= 0
    assert result.answers_scored >= 1
