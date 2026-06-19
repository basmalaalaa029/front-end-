"""CV generation — FastAPI routes."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Callable

from cv_agent.app.config import PipelineConfig, logger
from cv_generator.api.schemas import GenerateRequest, GenerateResponse, ResultResponse, StatusResponse
from cv_generator.api.session import SessionStatus, get_session_manager
from cv_generator.models.cv_schema import CVData, WizardStep1Request
from cv_generator.pdf_export import export_pdf_bytes
from cv_generator.services.cv_generator import build_template_result, run_enhancement_sync
from cv_generator.services.gemini_service import generate_cv_from_info
from cv_generator.services.template_service import fill_template
from cv_generator.validation import merge_enhancement
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_cv_routes(
    app: "FastAPI",
    *,
    cfg: PipelineConfig,
    pipeline_executor,
    check_rate_limit: Callable,
) -> None:
    from fastapi import Body, HTTPException, status

    _session_manager = get_session_manager()

    def _run_enhancement_background(
        session_id: str,
        cv_data: CVData,
        req_cfg: PipelineConfig,
    ) -> None:
        _session_manager.update_status(session_id, SessionStatus.RUNNING, "Enhancing with AI…")

        def _cb(msg: str) -> None:
            _session_manager.update_status(session_id, SessionStatus.RUNNING, msg)

        try:
            result = run_enhancement_sync(
                cv_data, session_id, req_cfg, on_progress=_cb,
            )
            _session_manager.complete(session_id, result)
            if result.node_errors:
                logger.warning(
                    "CV session=%s completed with template fallback: %s",
                    session_id, "; ".join(result.node_errors),
                )
            else:
                logger.info(
                    "CV session=%s completed with AI enhancement (%d ms)",
                    session_id, result.total_latency_ms,
                )
        except Exception as exc:
            logger.error("CV enhancement failed session=%s: %s", session_id, exc)
            template_md = _session_manager.get(session_id).template_cv if _session_manager.get(session_id) else ""
            fallback = build_template_result(cv_data, session_id, template_md)
            fallback.node_errors = [f"{type(exc).__name__}: {exc}"]
            _session_manager.complete(session_id, fallback)

    @app.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED, tags=["cv"])
    async def generate(req: GenerateRequest, request: Request) -> GenerateResponse:
        await check_rate_limit(request)
        cv_data = CVData.from_generate_request(req)
        if not cv_data.is_complete():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Profile must include full_name, target_role, and experience or projects.",
            )

        sid = req.session_id or str(uuid.uuid4())[:12]
        _session_manager.create(sid)

        template = fill_template(cv_data)
        template_md = template["markdown"]
        _session_manager.set_template(sid, template_md)

        req_cfg = PipelineConfig()
        req_cfg.db_path = cfg.db_path
        req_cfg.output_dir = cfg.output_dir
        req_cfg.gemini_api_key = cfg.gemini_api_key
        req_cfg.gemini_model = cfg.gemini_model
        req_cfg.gemini_temperature = cfg.gemini_temperature
        req_cfg.gemini_max_output_tokens = cfg.gemini_max_output_tokens

        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            pipeline_executor, _run_enhancement_background,
            sid, cv_data, req_cfg,
        )

        return GenerateResponse(
            session_id=sid,
            status=SessionStatus.RUNNING,
            template_cv=template_md,
            message=f"Template ready. Poll GET /status/{sid} for AI enhancement.",
        )

    @app.post("/generate-ai-cv", tags=["cv"])
    async def generate_ai_cv(req: WizardStep1Request, request: Request) -> dict:
        await check_rate_limit(request)
        cv_data = req.to_cv_data()
        if not cv_data.full_name or not cv_data.target_role:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="full_name and target_job are required.",
            )
        if not cv_data.education and not cv_data.experience and not cv_data.projects:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide at least education, experience, or projects.",
            )

        req_cfg = PipelineConfig()
        req_cfg.db_path = cfg.db_path
        req_cfg.output_dir = cfg.output_dir
        req_cfg.gemini_api_key = cfg.gemini_api_key
        req_cfg.gemini_model = cfg.gemini_model
        req_cfg.gemini_temperature = cfg.gemini_temperature
        req_cfg.gemini_max_output_tokens = cfg.gemini_max_output_tokens

        result = await generate_cv_from_info(cv_data.to_generation_input(), req_cfg)
        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.get("message", "CV generation failed"),
            )
        merged = merge_enhancement(cv_data, result.get("cv") or {})
        return {"status": "success", "cv": merged.to_generated_cv_json()}

    @app.get("/status/{session_id}", response_model=StatusResponse, tags=["cv"])
    async def get_status(session_id: str) -> StatusResponse:
        rec = _session_manager.get(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        return StatusResponse(
            session_id=rec.session_id, status=rec.status,
            created_at=rec.created_at, updated_at=rec.updated_at,
            progress_msgs=rec.progress_msgs, error=rec.error,
        )

    @app.get("/result/{session_id}", response_model=ResultResponse, tags=["cv"])
    async def get_result(session_id: str) -> ResultResponse:
        rec = _session_manager.get(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        if rec.status == SessionStatus.FAILED:
            return ResultResponse(
                session_id=session_id,
                status=rec.status,
                template_cv=rec.template_cv,
                error=rec.error,
            )
        if rec.status != SessionStatus.COMPLETED:
            return ResultResponse(
                session_id=session_id,
                status=rec.status,
                template_cv=rec.template_cv,
                final_cv=rec.template_cv,
                candidate_name="",
                target_role="",
            )
        r = rec.result
        assert r is not None
        return ResultResponse(
            session_id=r.session_id, status=SessionStatus.COMPLETED,
            candidate_name=r.candidate_name, target_role=r.target_role,
            total_iterations=r.total_iterations, final_cv=r.final_cv,
            template_cv=r.template_cv or rec.template_cv,
            enhanced_data=r.enhanced_data,
            final_scores=r.final_scores.model_dump() if r.final_scores else None,
            score_trajectory=r.score_trajectory, jd_keywords=r.jd_keywords,
            node_errors=r.node_errors, total_latency_ms=r.total_latency_ms,
        )

    @app.post("/pdf/direct", tags=["cv"])
    async def pdf_direct(
        markdown: str = Body(..., min_length=1),
        candidate_name: str = Body(""),
    ):
        from fastapi.responses import Response as FResponse

        try:
            pdf_bytes = export_pdf_bytes(markdown, candidate_name or "CV")
        except ImportError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        safe_name = (candidate_name or "CV").replace(" ", "_")
        return FResponse(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_CV.pdf"'},
        )

    @app.get("/result/{session_id}/pdf", tags=["cv"])
    async def download_pdf(session_id: str):
        from fastapi.responses import Response

        rec = _session_manager.get(session_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        if rec.status == SessionStatus.FAILED:
            raise HTTPException(status_code=400, detail=f"Session failed: {rec.error}")
        if rec.status != SessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=f"Session '{session_id}' is still {rec.status}.",
            )
        assert rec.result is not None
        pdf_bytes = export_pdf_bytes(rec.result.final_cv, rec.result.candidate_name)
        safe_name = rec.result.candidate_name.replace(" ", "_")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_CV.pdf"'},
        )

    @app.get("/sessions", tags=["cv"])
    async def list_sessions():
        return {"sessions": _session_manager.list_sessions()}
