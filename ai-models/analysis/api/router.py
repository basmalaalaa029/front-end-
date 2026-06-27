"""CV analysis FastAPI routes — POST /cv-analysis/analyze, GET /cv-analysis/analyze/{job_id}."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Literal

from fastapi import File, Form, HTTPException, UploadFile
from starlette.requests import Request

from analysis.api.schemas import AnalysisJobResponse, AnalysisRequest, AnalysisStartResponse
from analysis.api.service import (
    get_analysis_results,
    get_analysis_status,
    map_stage_for_frontend,
    start_analysis,
)
from analysis.cv_reader.parser import parse_resume_bytes

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_analysis_routes(
    app: "FastAPI",
    *,
    pipeline_executor,
    check_rate_limit: Callable,
) -> None:
    @app.post("/cv-analysis/analyze", response_model=AnalysisStartResponse, tags=["analysis"])
    async def analyze_cv(
        http_request: Request,
        file: UploadFile = File(...),
        target_role: str = Form("Target role"),
    ) -> AnalysisStartResponse:
        await check_rate_limit(http_request)

        body = await file.read()
        if not body:
            raise HTTPException(status_code=422, detail="Empty file.")
        filename = file.filename or "resume.pdf"

        try:
            resume_text = parse_resume_bytes(body, filename)
        except (ValueError, ImportError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        req = AnalysisRequest(resume_text=resume_text, target_role=target_role)
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                pipeline_executor,
                lambda: start_analysis(req, filename=filename),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            from cv_agent.app.config import logger
            logger.exception("POST /cv-analysis/analyze failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get(
        "/cv-analysis/analyze/{job_id}",
        response_model=AnalysisJobResponse,
        tags=["analysis"],
    )
    async def analysis_job_status(job_id: str) -> AnalysisJobResponse:
        status = get_analysis_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Session not found.")

        frontend_stage: Literal["parsing", "features", "judging", "done"] = map_stage_for_frontend(
            status.stage or "extracting"  # type: ignore[assignment]
        )

        if status.status == "failed":
            return AnalysisJobResponse(
                job_id=job_id,
                status="failed",
                stage="done",
                error=status.error or "Analysis failed.",
                elapsed_s=status.elapsed_s,
            )

        if status.status == "ready":
            results = get_analysis_results(job_id)
            if results is None or results.analysis is None:
                raise HTTPException(status_code=404, detail="Result not ready.")
            return AnalysisJobResponse(
                job_id=job_id,
                status="ready",
                stage="done",
                result=results.analysis.model_dump(),
                elapsed_s=status.elapsed_s,
            )

        return AnalysisJobResponse(
            job_id=job_id,
            status="processing",
            stage=frontend_stage,
            elapsed_s=status.elapsed_s,
        )
