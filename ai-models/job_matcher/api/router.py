"""Job matching — FastAPI routes."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable

from fastapi import File, Form, HTTPException, UploadFile
from job_matcher.api.schemas import MatchRequest, MatchResponse, MatchResultsResponse
from job_matcher.api.service import get_match_results, run_job_match
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI
    from cv_agent.app.config import PipelineConfig


def register_job_match_routes(
    app: "FastAPI",
    *,
    cfg: "PipelineConfig",
    pipeline_executor,
    check_rate_limit: Callable,
) -> None:
    @app.post("/jobs/match", response_model=MatchResponse, tags=["job_match"])
    async def match_jobs(req: MatchRequest, request: Request) -> MatchResponse:
        await check_rate_limit(request)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                pipeline_executor,
                lambda: run_job_match(req, config=cfg),
            )
            return MatchResponse(
                session_id=result.session_id,
                status=result.status,
                total_jobs=len(result.jobs),
                message=f"Matched {len(result.jobs)} roles in {result.latency_ms}ms.",
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            from cv_agent.app.config import logger
            logger.exception("POST /jobs/match failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/jobs/match/upload", response_model=MatchResponse, tags=["job_match"])
    async def match_jobs_upload(
        request: Request,
        file: UploadFile = File(...),
        target_role: str = Form(""),
        location: str = Form(""),
    ) -> MatchResponse:
        await check_rate_limit(request)
        from cv_analysis.parsing.file_parsing import parse_resume_bytes

        raw = await file.read()
        filename = file.filename or "cv.pdf"
        try:
            cv_text = parse_resume_bytes(raw, filename)
        except (ValueError, ImportError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        req = MatchRequest(cv_text=cv_text, target_role=target_role, location=location)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                pipeline_executor,
                lambda: run_job_match(req, config=cfg),
            )
            return MatchResponse(
                session_id=result.session_id,
                status=result.status,
                total_jobs=len(result.jobs),
                message=f"Matched {len(result.jobs)} roles in {result.latency_ms}ms.",
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            from cv_agent.app.config import logger
            logger.exception("POST /jobs/match/upload failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/jobs/results/{session_id}", response_model=MatchResultsResponse, tags=["job_match"])
    async def job_results(session_id: str) -> MatchResultsResponse:
        try:
            return get_match_results(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
