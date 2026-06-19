"""Virtual interview — FastAPI routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from interview.api.schemas import (
    EvaluationResult,
    InterviewSessionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from interview.api.service import (
    evaluate_interview,
    get_session,
    start_interview,
    submit_answer,
)
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_interview_routes(
    app: "FastAPI",
    *,
    check_rate_limit: Callable,
) -> None:
    from fastapi import HTTPException

    @app.post("/interview/start", response_model=StartInterviewResponse, tags=["interview"])
    async def interview_start(req: StartInterviewRequest, request: Request) -> StartInterviewResponse:
        await check_rate_limit(request)
        try:
            return start_interview(req)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/interview/{session_id}", response_model=InterviewSessionResponse, tags=["interview"])
    async def interview_get(session_id: str) -> InterviewSessionResponse:
        try:
            return get_session(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/interview/{session_id}/answer",
        response_model=SubmitAnswerResponse,
        tags=["interview"],
    )
    async def interview_answer(
        session_id: str,
        req: SubmitAnswerRequest,
        request: Request,
    ) -> SubmitAnswerResponse:
        await check_rate_limit(request)
        try:
            return submit_answer(session_id, req)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post(
        "/interview/{session_id}/evaluate",
        response_model=EvaluationResult,
        tags=["interview"],
    )
    async def interview_evaluate(session_id: str, request: Request) -> EvaluationResult:
        await check_rate_limit(request)
        try:
            return evaluate_interview(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
