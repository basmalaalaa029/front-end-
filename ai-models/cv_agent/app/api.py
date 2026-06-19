"""
cv_agent.app.api — FastAPI application factory and system routes.
"""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from cv_agent.app.config import PipelineConfig, _FASTAPI_AVAILABLE, logger
from cv_agent.app.config import (
    _FAISS_AVAILABLE, _SENTENCE_AVAILABLE, _SKLEARN_AVAILABLE,
    _REPORTLAB_AVAILABLE, _MISTUNE_AVAILABLE,
)
from cv_agent.app.cache import get_cache as get_cv_cache
from cv_generator.api.session import get_session_manager

_session_manager = get_session_manager()


if _FASTAPI_AVAILABLE:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    class HealthResponse(BaseModel):
        status: str
        cache_stats: Dict[str, int]
        active_sessions: int
        cv_writer_ready: bool = False
        analysis_ready: bool = False
        analysis_queue_size: int = 0
        features: Dict[str, bool]

    _generation_executor = ThreadPoolExecutor(
        max_workers=int(os.getenv("GENERATION_WORKERS", os.getenv("PIPELINE_WORKERS", "2"))),
        thread_name_prefix="generation",
    )
    _analysis_executor = ThreadPoolExecutor(
        max_workers=int(os.getenv("ANALYSIS_WORKERS", os.getenv("PIPELINE_WORKERS", "2"))),
        thread_name_prefix="analysis",
    )

    def create_app(default_cfg: Optional[PipelineConfig] = None) -> "FastAPI":
        from cv_analysis.api.router import register_cv_analysis_routes
        from cv_analysis.config import get_cv_analysis_config
        from cv_analysis.judges.model_runtime import get_analysis_runtime
        from cv_analysis.judges.queue import inference_queue
        from cv_agent.app.auth import register_jwt_middleware
        from cv_generator.api.router import register_cv_routes
        from interview.api.router import register_interview_routes
        from job_matcher.api.router import register_job_match_routes

        _cfg = default_cfg or PipelineConfig()
        _analysis_cfg = get_cv_analysis_config()

        app = FastAPI(
            title="CV Agent SaaS API",
            description="Agentic CV Generation — feature-isolated slices + FastAPI",
            version="8.0.0",
        )

        _raw_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:8080",
        )
        _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
        _RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "20"))
        _rate_buckets: Dict[str, List[float]] = {}
        _rate_lock = threading.Lock()

        async def _check_rate_limit(request: Request) -> None:
            from fastapi import HTTPException
            if _RATE_LIMIT_RPM <= 0:
                return
            path = request.url.path
            if (
                path == "/health"
                or path.startswith("/status/")
                or path.startswith("/cv-analysis/analyze/")
            ):
                return
            client_ip = (
                request.headers.get("X-Forwarded-For")
                or (request.client.host if request.client else "unknown")
            )
            now = time.monotonic()
            with _rate_lock:
                timestamps = [t for t in _rate_buckets.get(client_ip, []) if now - t < 60.0]
                if len(timestamps) >= _RATE_LIMIT_RPM:
                    _rate_buckets[client_ip] = timestamps
                    raise HTTPException(status_code=429, detail=f"Rate limit: {_RATE_LIMIT_RPM}/min")
                timestamps.append(now)
                _rate_buckets[client_ip] = timestamps

        register_jwt_middleware(app)

        @app.middleware("http")
        async def _request_timing(request: Request, call_next: Any) -> Any:
            t0 = time.perf_counter()
            res = await call_next(request)
            res.headers["X-Response-Time-Ms"] = str(int((time.perf_counter() - t0) * 1000))
            return res

        app.add_middleware(
            CORSMiddleware,
            allow_origins=_allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        )

        @app.on_event("startup")
        async def _startup_cv_analysis() -> None:
            if _analysis_cfg.warmup_on_startup:
                runtime = get_analysis_runtime()
                threading.Thread(
                    target=runtime.start,
                    args=(_analysis_cfg,),
                    daemon=True,
                    name="cv-analysis-llama-start",
                ).start()
                inference_queue.mark_ready()
                inference_queue.start()

        @app.on_event("shutdown")
        async def _shutdown_cv_analysis() -> None:
            get_analysis_runtime().stop()

        @app.get("/health", response_model=HealthResponse, tags=["system"])
        async def health() -> HealthResponse:
            an_rt = get_analysis_runtime()
            degraded = not inference_queue.is_alive
            gemini_ready = bool((_cfg.gemini_api_key or "").strip())
            return HealthResponse(
                status="degraded" if degraded else "ok",
                cache_stats=get_cv_cache(_cfg).stats(),
                active_sessions=len(_session_manager.list_sessions()),
                cv_writer_ready=gemini_ready,
                analysis_ready=an_rt.ready,
                analysis_queue_size=inference_queue.queue_size,
                features={
                    "faiss": _FAISS_AVAILABLE,
                    "sentence_transformers": _SENTENCE_AVAILABLE,
                    "sklearn": _SKLEARN_AVAILABLE,
                    "pdf_export": _REPORTLAB_AVAILABLE,
                    "mistune": _MISTUNE_AVAILABLE,
                    "gemini_cv": gemini_ready,
                },
            )

        @app.delete("/cache", tags=["system"])
        async def clear_cache() -> Dict[str, str]:
            get_cv_cache(_cfg).clear()
            from cv_analysis.judges.cache import get_cache
            get_cache().clear()
            return {"message": "Cache cleared."}

        register_cv_analysis_routes(
            app, cfg=_analysis_cfg, pipeline_executor=_analysis_executor,
            check_rate_limit=_check_rate_limit,
        )
        register_cv_routes(
            app, cfg=_cfg, pipeline_executor=_generation_executor,
            check_rate_limit=_check_rate_limit,
        )
        register_job_match_routes(
            app, cfg=_cfg, pipeline_executor=_analysis_executor,
            check_rate_limit=_check_rate_limit,
        )
        register_interview_routes(app, check_rate_limit=_check_rate_limit)

        return app

    app = create_app()

else:
    app = None  # type: ignore[assignment]
