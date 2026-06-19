"""Virtual interview feature — request/response schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    cv_text: str = Field(..., min_length=50)
    target_role: str = "Software Engineer"
    company: str = ""


class InterviewQuestion(BaseModel):
    id: str
    text: str
    category: str = "behavioral"


class StartInterviewResponse(BaseModel):
    session_id: str
    status: str = "active"
    questions: List[InterviewQuestion] = Field(default_factory=list)
    message: str = ""


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer: str = Field(..., min_length=10)


class AnswerScore(BaseModel):
    clarity: int = Field(ge=0, le=100, default=0)
    structure: int = Field(ge=0, le=100, default=0)
    relevance: int = Field(ge=0, le=100, default=0)
    overall: int = Field(ge=0, le=100, default=0)
    feedback: str = ""


class SubmitAnswerResponse(BaseModel):
    session_id: str
    question_id: str
    score: AnswerScore
    next_question: Optional[InterviewQuestion] = None


class EvaluationResult(BaseModel):
    session_id: str
    status: Literal["active", "completed"] = "completed"
    overall_score: int = Field(ge=0, le=100, default=0)
    answers_scored: int = 0
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    per_answer: List[AnswerScore] = Field(default_factory=list)


class InterviewSessionResponse(BaseModel):
    session_id: str
    status: str
    target_role: str = ""
    company: str = ""
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers_count: int = 0
    current_question: Optional[InterviewQuestion] = None
