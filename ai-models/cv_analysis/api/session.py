"""In-memory analysis jobs with stage tracking."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config


class JobStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class JobStage(str, Enum):
    PARSING = "parsing"
    FEATURES = "features"
    JUDGING = "judging"
    DONE = "done"


@dataclass
class AnalysisJob:
    job_id: str
    status: JobStatus = JobStatus.PROCESSING
    stage: JobStage = JobStage.PARSING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class AnalysisJobStore:
    def __init__(self, max_jobs: int = 200, ttl_seconds: int = 3600) -> None:
        self._jobs: Dict[str, AnalysisJob] = {}
        self._lock = threading.Lock()
        self._max = max_jobs
        self._ttl = ttl_seconds

    def create(self) -> AnalysisJob:
        job = AnalysisJob(job_id=str(uuid.uuid4()))
        with self._lock:
            self._purge_expired()
            if len(self._jobs) >= self._max:
                oldest = min(self._jobs.values(), key=lambda j: j.created_at)
                del self._jobs[oldest.job_id]
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[AnalysisJob]:
        with self._lock:
            self._purge_expired()
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for k, v in kwargs.items():
                    setattr(job, k, v)

    def _purge_expired(self) -> None:
        if self._ttl <= 0:
            return
        now = time.time()
        expired = [jid for jid, j in self._jobs.items() if now - j.created_at > self._ttl]
        for jid in expired:
            del self._jobs[jid]


_store: Optional[AnalysisJobStore] = None


def get_job_store(cfg: Optional[CVAnalysisConfig] = None) -> AnalysisJobStore:
    global _store
    if _store is None:
        c = cfg or get_cv_analysis_config()
        _store = AnalysisJobStore(max_jobs=c.job_max_sessions, ttl_seconds=c.job_ttl_seconds)
    return _store
