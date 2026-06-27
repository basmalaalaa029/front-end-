"""In-memory store for CV analysis sessions."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from analysis.config import SESSION_MAX_SESSIONS, SESSION_TTL_SECONDS
from analysis.validation.result_validator import AnalysisResult


class AnalysisStage(str, Enum):
    EXTRACTING = "extracting"
    CALLING_MODEL = "calling_model"
    VALIDATING = "validating"
    DONE = "done"


class AnalysisStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class AnalysisSession:
    session_id: str
    status: AnalysisStatus = AnalysisStatus.PROCESSING
    stage: AnalysisStage = AnalysisStage.EXTRACTING
    filename: str = ""
    analysis: Optional[AnalysisResult] = None
    warnings: list = field(default_factory=list)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class SessionManager:
    def __init__(self, max_sessions: int = SESSION_MAX_SESSIONS, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._sessions: Dict[str, AnalysisSession] = {}
        self._lock = threading.Lock()
        self._max = max_sessions
        self._ttl = ttl_seconds

    def create(self) -> AnalysisSession:
        session = AnalysisSession(session_id=str(uuid.uuid4())[:12])
        with self._lock:
            self._purge_expired()
            if len(self._sessions) >= self._max:
                oldest = min(self._sessions.values(), key=lambda s: s.created_at)
                del self._sessions[oldest.session_id]
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[AnalysisSession]:
        with self._lock:
            self._purge_expired()
            return self._sessions.get(session_id)

    def update(self, session_id: str, **kwargs: Any) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                for k, v in kwargs.items():
                    setattr(session, k, v)

    def _purge_expired(self) -> None:
        if self._ttl <= 0:
            return
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.created_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
