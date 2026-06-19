"""In-memory store for job match sessions."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from job_matcher.api.schemas import MatchedJob


class MatchSession(BaseModel):
    session_id: str
    status: str = "completed"
    jobs: List[MatchedJob] = Field(default_factory=list)
    target_role: str = ""
    latency_ms: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


class MatchSessionManager:
    def __init__(self, max_sessions: int = 500) -> None:
        self._sessions: Dict[str, MatchSession] = {}
        self._lock = threading.Lock()
        self._max = max_sessions

    def create(self, session_id: str, session: MatchSession) -> MatchSession:
        with self._lock:
            if len(self._sessions) >= self._max and self._sessions:
                oldest = min(self._sessions.items(), key=lambda x: x[1].created_at)
                del self._sessions[oldest[0]]
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[MatchSession]:
        with self._lock:
            return self._sessions.get(session_id)


_manager = MatchSessionManager()


def get_match_session_manager() -> MatchSessionManager:
    return _manager
