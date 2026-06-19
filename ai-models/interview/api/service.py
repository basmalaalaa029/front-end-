"""Interview session orchestration."""

from __future__ import annotations

import uuid
from typing import Optional

from interview.api.schemas import (
    EvaluationResult,
    InterviewQuestion,
    InterviewSessionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from interview.api.session import InterviewRecord, get_interview_session_manager
from interview.evaluation.scoring import evaluate_session, score_answer
from interview.questions.generator import generate_questions


def start_interview(req: StartInterviewRequest) -> StartInterviewResponse:
    text = req.cv_text.strip()
    if len(text) < 50:
        raise ValueError("CV text is too short — provide at least 50 characters.")

    session_id = str(uuid.uuid4())[:12]
    questions = generate_questions(text, req.target_role, req.company)

    record = InterviewRecord(
        session_id=session_id,
        target_role=req.target_role,
        company=req.company,
        cv_text=text,
        questions=questions,
    )
    get_interview_session_manager().create(record)

    return StartInterviewResponse(
        session_id=session_id,
        status="active",
        questions=questions,
        message=f"Interview started with {len(questions)} questions.",
    )


def get_session(session_id: str) -> InterviewSessionResponse:
    rec = get_interview_session_manager().get(session_id)
    if rec is None:
        raise ValueError(f"Session '{session_id}' not found.")

    current = None
    if rec.status == "active" and rec.question_index < len(rec.questions):
        q = rec.questions[rec.question_index]
        if q.id not in rec.answers:
            current = q

    return InterviewSessionResponse(
        session_id=rec.session_id,
        status=rec.status,
        target_role=rec.target_role,
        company=rec.company,
        questions=rec.questions,
        answers_count=len(rec.answers),
        current_question=current,
    )


def submit_answer(session_id: str, req: SubmitAnswerRequest) -> SubmitAnswerResponse:
    rec = get_interview_session_manager().get(session_id)
    if rec is None:
        raise ValueError(f"Session '{session_id}' not found.")
    if rec.status != "active":
        raise ValueError("Interview session is already completed.")

    question = next((q for q in rec.questions if q.id == req.question_id), None)
    if question is None:
        raise ValueError(f"Question '{req.question_id}' not found.")

    score = score_answer(req.answer, question, rec.cv_text)
    rec.answers[req.question_id] = req.answer.strip()
    rec.scores[req.question_id] = score

    if rec.question_index < len(rec.questions) - 1:
        rec.question_index += 1

    next_q: Optional[InterviewQuestion] = None
    for q in rec.questions[rec.question_index:]:
        if q.id not in rec.answers:
            next_q = q
            break

    if len(rec.answers) >= len(rec.questions):
        rec.status = "completed"

    get_interview_session_manager().update(rec)

    return SubmitAnswerResponse(
        session_id=session_id,
        question_id=req.question_id,
        score=score,
        next_question=next_q,
    )


def evaluate_interview(session_id: str) -> EvaluationResult:
    rec = get_interview_session_manager().get(session_id)
    if rec is None:
        raise ValueError(f"Session '{session_id}' not found.")

    per_answer = list(rec.scores.values())
    overall, strengths, improvements = evaluate_session(per_answer)
    rec.status = "completed"
    get_interview_session_manager().update(rec)

    return EvaluationResult(
        session_id=session_id,
        status="completed",
        overall_score=overall,
        answers_scored=len(per_answer),
        strengths=strengths,
        improvements=improvements,
        per_answer=per_answer,
    )
