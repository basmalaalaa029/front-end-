"""CV generation — async session tracking."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from cv_generator.models.pipeline import PipelineResult


class SessionStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionRecord(BaseModel):
    session_id: str
    status: str = SessionStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    progress_msgs: List[str] = Field(default_factory=list)
    template_cv: str = ""
    result: Optional[PipelineResult] = None
    error: Optional[str] = None


class SessionManager:
    def __init__(self, max_sessions: int = 1000) -> None:
        self._sessions: Dict[str, SessionRecord] = {}
        self._lock = threading.Lock()
        self._max = max_sessions

    def create(self, session_id: str) -> SessionRecord:
        rec = SessionRecord(session_id=session_id)
        with self._lock:
            if len(self._sessions) >= self._max:
                completed = [
                    (k, v) for k, v in self._sessions.items()
                    if v.status in (SessionStatus.COMPLETED, SessionStatus.FAILED)
                ]
                if completed:
                    oldest = min(completed, key=lambda x: x[1].updated_at)
                    del self._sessions[oldest[0]]
            self._sessions[session_id] = rec
        return rec

    def get(self, session_id: str) -> Optional[SessionRecord]:
        with self._lock:
            return self._sessions.get(session_id)

    def update_status(self, session_id: str, status: str, msg: Optional[str] = None) -> None:
        with self._lock:
            rec = self._sessions.get(session_id)
            if rec:
                rec.status = status
                rec.updated_at = datetime.now().isoformat()
                if msg:
                    rec.progress_msgs.append(msg)

    def set_template(self, session_id: str, template_cv: str) -> None:
        with self._lock:
            rec = self._sessions.get(session_id)
            if rec:
                rec.template_cv = template_cv
                rec.status = SessionStatus.RUNNING
                rec.updated_at = datetime.now().isoformat()

    def complete(self, session_id: str, result: PipelineResult) -> None:
        with self._lock:
            rec = self._sessions.get(session_id)
            if rec:
                rec.status = SessionStatus.COMPLETED
                rec.result = result
                rec.updated_at = datetime.now().isoformat()

    def fail(self, session_id: str, error: str) -> None:
        with self._lock:
            rec = self._sessions.get(session_id)
            if rec:
                rec.status = SessionStatus.FAILED
                rec.error = error
                rec.updated_at = datetime.now().isoformat()

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "session_id": v.session_id,
                    "status": v.status,
                    "created_at": v.created_at,
                    "updated_at": v.updated_at,
                }
                for v in self._sessions.values()
            ]


_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    return _session_manager
