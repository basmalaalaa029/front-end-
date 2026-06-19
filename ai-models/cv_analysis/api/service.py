"""CV analysis async job service."""

from __future__ import annotations

import threading
import time
from typing import Optional

from cv_analysis.api.schemas import AnalysisJobResponse, AnalysisStartResponse
from cv_analysis.api.session import JobStage, JobStatus, get_job_store
from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config
from cv_analysis.pipeline import run_analysis_pipeline
from cv_agent.app.config import logger


def _run_job_background(
    job_id: str,
    *,
    cv_text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: str = "resume.pdf",
    jd_text: str = "",
    target_role: str = "Target role",
    cfg: Optional[CVAnalysisConfig] = None,
) -> None:
    store = get_job_store(cfg)
    try:

        def on_stage(stage: str) -> None:
            store.update(job_id, stage=JobStage(stage))

        result = run_analysis_pipeline(
            cv_text=cv_text,
            file_bytes=file_bytes,
            filename=filename,
            job_description=jd_text,
            target_role=target_role,
            cfg=cfg,
            on_stage=on_stage,
        )
        store.update(
            job_id,
            status=JobStatus.READY,
            stage=JobStage.DONE,
            result=result,
            completed_at=time.time(),
        )
        logger.info("[cv_analysis] Job %s complete", job_id[:8])
    except Exception as exc:
        logger.exception("[cv_analysis] Job %s failed", job_id[:8])
        store.update(
            job_id,
            status=JobStatus.FAILED,
            stage=JobStage.DONE,
            error=str(exc),
            completed_at=time.time(),
        )


def start_analysis_job(
    *,
    cv_text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: str = "resume.pdf",
    jd_text: str = "",
    target_role: str = "Target role",
    cfg: Optional[CVAnalysisConfig] = None,
) -> AnalysisStartResponse:
    cfg = cfg or get_cv_analysis_config()
    job = get_job_store(cfg).create()
    threading.Thread(
        target=_run_job_background,
        kwargs={
            "job_id": job.job_id,
            "cv_text": cv_text,
            "file_bytes": file_bytes,
            "filename": filename,
            "jd_text": jd_text,
            "target_role": target_role,
            "cfg": cfg,
        },
        daemon=True,
        name=f"cv-analysis-{job.job_id[:8]}",
    ).start()
    return AnalysisStartResponse(job_id=job.job_id)


def get_job_status(job_id: str) -> Optional[AnalysisJobResponse]:
    job = get_job_store().get(job_id)
    if not job:
        return None
    elapsed = time.time() - job.created_at
    return AnalysisJobResponse(
        job_id=job.job_id,
        status=job.status.value,
        stage=job.stage.value,
        result=job.result,
        error=job.error,
        elapsed_s=round(elapsed, 1),
    )
