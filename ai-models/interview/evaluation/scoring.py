"""Per-answer and session-level interview scoring."""

from __future__ import annotations

import re
from typing import List

from interview.api.schemas import AnswerScore, InterviewQuestion
from interview.scoring.answer_quality import score_answer_quality


def score_answer(answer: str, question: InterviewQuestion, cv_text: str) -> AnswerScore:
    text = answer.strip()
    overall = score_answer_quality(text, question.text)

    relevance = 50
    q_words = set(re.findall(r"[a-z]{4,}", question.text.lower()))
    a_words = set(re.findall(r"[a-z]{4,}", text.lower()))
    if q_words:
        overlap = len(q_words & a_words) / len(q_words)
        relevance = min(100, int(50 + overlap * 50))

    cv_words = set(re.findall(r"[a-z]{4,}", cv_text.lower()))
    if cv_words and a_words:
        cv_overlap = len(cv_words & a_words) / min(len(cv_words), 30)
        relevance = min(100, int((relevance + cv_overlap * 100) / 2))

    clarity = min(100, overall + 5)
    structure = min(100, overall)
    overall = int((clarity + structure + relevance) / 3)

    if overall >= 75:
        feedback = "Strong answer — clear and relevant."
    elif overall >= 55:
        feedback = "Decent answer — add more specifics and metrics."
    else:
        feedback = "Needs work — structure your answer with situation, action, result."

    return AnswerScore(
        clarity=clarity,
        structure=structure,
        relevance=relevance,
        overall=overall,
        feedback=feedback,
    )


def evaluate_session(scores: List[AnswerScore]) -> tuple[int, List[str], List[str]]:
    if not scores:
        return 0, [], ["No answers submitted yet."]

    overall = int(sum(s.overall for s in scores) / len(scores))
    strengths: List[str] = []
    improvements: List[str] = []

    avg_clarity = sum(s.clarity for s in scores) / len(scores)
    avg_structure = sum(s.structure for s in scores) / len(scores)
    avg_relevance = sum(s.relevance for s in scores) / len(scores)

    if avg_clarity >= 70:
        strengths.append("Clear communication throughout answers.")
    else:
        improvements.append("Work on concise, direct phrasing.")

    if avg_structure >= 70:
        strengths.append("Well-structured responses with logical flow.")
    else:
        improvements.append("Use STAR format: Situation, Task, Action, Result.")

    if avg_relevance >= 70:
        strengths.append("Answers stay relevant to the questions asked.")
    else:
        improvements.append("Tie answers more closely to the role and your CV experience.")

    if overall >= 80 and not strengths:
        strengths.append("Consistent performance across all questions.")

    return overall, strengths[:3], improvements[:3]
