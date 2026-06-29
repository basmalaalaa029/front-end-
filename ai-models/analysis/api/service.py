"""CV analysis — orchestrates the analysis pipeline."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from analysis.api.schemas import (
    AnalysisRequest,
    AnalysisResultsResponse,
    AnalysisStartResponse,
    AnalysisStatusResponse,
)
from analysis.api.session import AnalysisStage, AnalysisStatus, get_session_manager

log = logging.getLogger("analysis")

_FRONTEND_STAGE_MAP = {
    "extracting": "parsing",
    "calling_model": "judging",
    "validating": "judging",
    "done": "done",
}


def map_stage_for_frontend(internal_stage: str) -> str:
    return _FRONTEND_STAGE_MAP.get(internal_stage, "parsing")


def _call_analysis_model(
    resume_text: str,
    max_new_tokens: int,
    target_role: str = "",
) -> tuple[Optional[dict], str]:
    from analysis.model_client.modal_client import call_analysis_model, get_last_modal_error

    response = call_analysis_model(
        resume_text,
        max_new_tokens=max_new_tokens,
        target_role=target_role,
    )
    if response is not None:
        return response, ""

    modal_err = get_last_modal_error() or "Modal analysis unavailable"
    return None, modal_err


def _run_full_pipeline(
    resume_text: str,
    target_role: str = "",
    on_stage: Optional[Callable[[str], None]] = None,
) -> tuple:
    from analysis.config import MODAL_MAX_NEW_TOKENS
    from analysis.validation.result_validator import validate_result

    if on_stage:
        on_stage("calling_model")

    token_budgets = [MODAL_MAX_NEW_TOKENS, min(MODAL_MAX_NEW_TOKENS + 512, 2048)]
    last_warnings: list = []
    last_raw: str | None = None

    for attempt, max_new_tokens in enumerate(token_budgets, start=1):
        model_response, provider_error = _call_analysis_model(
            resume_text,
            max_new_tokens=max_new_tokens,
            target_role=target_role,
        )
        if model_response is None:
            raise ValueError(provider_error or "Could not reach the analysis model, or it returned an error.")

        if on_stage:
            on_stage("validating")

        analysis, warnings = validate_result(model_response["parsed"])
        if analysis is not None:
            if attempt > 1:
                log.info("Analysis validation succeeded on retry (attempt %d)", attempt)
            return analysis, warnings

        last_warnings = warnings
        last_raw = model_response.get("raw")
        log.warning(
            "Analysis result validation failed (attempt %d/%d): %s",
            attempt,
            len(token_budgets),
            warnings,
        )

    log.warning("Analysis result validation failed after retries. Raw model output: %s", last_raw)
    detail = last_warnings[0] if last_warnings else "missing actionable recommendations"
    raise ValueError(f"The analysis model returned an incomplete response: {detail}")


def _run_analysis_background(
    session_id: str,
    resume_text: str,
    filename: str,
    target_role: str = "",
) -> None:
    store = get_session_manager()
    try:
        def on_stage(stage: str) -> None:
            store.update(session_id, stage=AnalysisStage(stage))
            log.info("[analysis] Session %s stage=%s", session_id, stage)

        analysis, warnings = _run_full_pipeline(
            resume_text,
            target_role=target_role,
            on_stage=on_stage,
        )
        store.update(
            session_id,
            status=AnalysisStatus.READY,
            stage=AnalysisStage.DONE,
            filename=filename,
            analysis=analysis,
            warnings=warnings,
            completed_at=time.time(),
        )
        log.info("[analysis] Session %s complete", session_id)
    except Exception as exc:
        log.exception("[analysis] Session %s failed", session_id)
        store.update(
            session_id,
            status=AnalysisStatus.FAILED,
            stage=AnalysisStage.DONE,
            error=str(exc),
            completed_at=time.time(),
        )


def start_analysis(req: AnalysisRequest, filename: str = "resume") -> AnalysisStartResponse:
    text = req.resume_text.strip()
    if len(text) < 50:
        raise ValueError("Resume text is too short — provide at least 50 characters.")

    session = get_session_manager().create()
    threading.Thread(
        target=_run_analysis_background,
        args=(session.session_id, text, filename, req.target_role),
        daemon=True,
        name=f"analysis-{session.session_id}",
    ).start()
    return AnalysisStartResponse(job_id=session.session_id)


def get_analysis_status(session_id: str) -> Optional[AnalysisStatusResponse]:
    session = get_session_manager().get(session_id)
    if not session:
        return None
    elapsed = time.time() - session.created_at
    return AnalysisStatusResponse(
        session_id=session.session_id,
        status=session.status.value,
        stage=session.stage.value,
        elapsed_s=round(elapsed, 1),
        error=session.error,
    )


def get_analysis_results(session_id: str) -> Optional[AnalysisResultsResponse]:
    session = get_session_manager().get(session_id)
    if not session or session.status != AnalysisStatus.READY:
        return None
    return AnalysisResultsResponse(
        session_id=session.session_id,
        filename=session.filename,
        analysis=session.analysis,
        warnings=session.warnings,
        error=session.error,
    )
