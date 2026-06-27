"""In-memory store for job match sessions."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from job_matcher.api.schemas import MatchedJob


class MatchStage(str, Enum):
    PARSING = "parsing"
    FETCHING = "fetching"
    RANKING = "ranking"
    EXPLAINING = "explaining"
    DONE = "done"


class MatchStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class MatchSession:
    session_id: str
    status: MatchStatus = MatchStatus.PROCESSING
    stage: MatchStage = MatchStage.PARSING
    jobs: List[MatchedJob] = field(default_factory=list)
    target_role: str = ""
    latency_ms: int = 0
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class SessionManager:
    def __init__(self, max_sessions: int = 500, ttl_seconds: int = 3600) -> None:
        self._sessions: Dict[str, MatchSession] = {}
        self._lock = threading.Lock()
        self._max = max_sessions
        self._ttl = ttl_seconds

    def create(self) -> MatchSession:
        session = MatchSession(session_id=str(uuid.uuid4())[:12])
        with self._lock:
            self._purge_expired()
            if len(self._sessions) >= self._max:
                oldest = min(self._sessions.values(), key=lambda s: s.created_at)
                del self._sessions[oldest.session_id]
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[MatchSession]:
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
