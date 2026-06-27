"""Job matching — FastAPI routes."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable

from cv_agent.app.config import PipelineConfig
from fastapi import File, Form, HTTPException, UploadFile
from job_matcher.api.schemas import (
    MatchRequest,
    MatchResultsResponse,
    MatchStartResponse,
    MatchStatusResponse,
)
from job_matcher.api.service import get_match_results, get_match_status, start_job_match
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_job_match_routes(
    app: "FastAPI",
    *,
    cfg: PipelineConfig,
    pipeline_executor,
    check_rate_limit: Callable,
) -> None:
    @app.post("/jobs/match", response_model=MatchStartResponse, tags=["job_match"])
    async def match_jobs(req: MatchRequest, request: Request) -> MatchStartResponse:
        await check_rate_limit(request)
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                pipeline_executor,
                lambda: start_job_match(req, config=cfg),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            from cv_agent.app.config import logger
            logger.exception("POST /jobs/match failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/jobs/match/upload", response_model=MatchStartResponse, tags=["job_match"])
    async def match_jobs_upload(
        request: Request,
        file: UploadFile = File(...),
        target_role: str = Form(""),
        location: str = Form(""),
    ) -> MatchStartResponse:
        await check_rate_limit(request)
        from analysis.parsing.file_parsing import parse_resume_bytes

        raw = await file.read()
        filename = file.filename or "cv.pdf"
        try:
            cv_text = parse_resume_bytes(raw, filename)
        except (ValueError, ImportError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        req = MatchRequest(cv_text=cv_text, target_role=target_role, location=location)
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                pipeline_executor,
                lambda: start_job_match(req, config=cfg),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            from cv_agent.app.config import logger
            logger.exception("POST /jobs/match/upload failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get(
        "/jobs/status/{session_id}",
        response_model=MatchStatusResponse,
        tags=["job_match"],
    )
    async def job_match_status(session_id: str) -> MatchStatusResponse:
        result = get_match_status(session_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        return result

    async def _job_match_result(session_id: str) -> MatchResultsResponse:
        status = get_match_status(session_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        if status.status == "failed":
            raise HTTPException(status_code=400, detail=status.error or "Job match failed.")
        if status.status != "ready":
            raise HTTPException(status_code=404, detail="Result not ready.")
        result = get_match_results(session_id)
        assert result is not None
        return result

    @app.get(
        "/jobs/result/{session_id}",
        response_model=MatchResultsResponse,
        tags=["job_match"],
    )
    async def job_match_result(session_id: str) -> MatchResultsResponse:
        return await _job_match_result(session_id)

    @app.get(
        "/jobs/results/{session_id}",
        response_model=MatchResultsResponse,
        tags=["job_match"],
    )
    async def job_match_results_alias(session_id: str) -> MatchResultsResponse:
        """Legacy path used by older frontends."""
        return await _job_match_result(session_id)
