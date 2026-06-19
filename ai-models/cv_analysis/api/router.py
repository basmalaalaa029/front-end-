"""CV analysis FastAPI routes — POST /cv-analysis/analyze, GET /cv-analysis/analyze/{job_id}."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Optional

from cv_analysis.api.schemas import AnalysisJobResponse, AnalysisStartResponse
from cv_analysis.api.service import get_job_status, start_analysis_job
from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from fastapi import File, Form, HTTPException, UploadFile
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_cv_analysis_routes(
    app: "FastAPI",
    *,
    cfg: Optional[CVAnalysisConfig] = None,
    pipeline_executor=None,
    check_rate_limit: Callable,
) -> None:
    analysis_cfg = cfg or get_cv_analysis_config()

    @app.post("/cv-analysis/analyze", response_model=AnalysisStartResponse, tags=["cv_analysis"])
    async def analyze_cv(
        http_request: Request,
        file: Optional[UploadFile] = File(None),
        jd_text: str = Form(""),
        cv_text: str = Form(""),
    ) -> AnalysisStartResponse:
        await check_rate_limit(http_request)

        if file is None and not (cv_text or "").strip():
            raise HTTPException(status_code=422, detail="Provide file upload or cv_text.")

        if file is not None:
            body = await file.read()
            if not body:
                raise HTTPException(status_code=422, detail="Empty file.")
            filename = file.filename or "resume.pdf"
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                pipeline_executor,
                lambda: start_analysis_job(
                    file_bytes=body, filename=filename, jd_text=jd_text, cfg=analysis_cfg,
                ),
            )

        if len(cv_text.strip()) < 50:
            raise HTTPException(status_code=422, detail="CV text must be at least 50 characters.")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            pipeline_executor,
            lambda: start_analysis_job(cv_text=cv_text, jd_text=jd_text, cfg=analysis_cfg),
        )

    @app.get("/cv-analysis/analyze/{job_id}", response_model=AnalysisJobResponse, tags=["cv_analysis"])
    async def analyze_job_status(job_id: str, http_request: Request) -> AnalysisJobResponse:
        await check_rate_limit(http_request)
        result = get_job_status(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Job not found.")
        return result
