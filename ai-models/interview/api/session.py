"""In-memory interview session store."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from interview.api.schemas import AnswerScore, InterviewQuestion


class InterviewRecord(BaseModel):
    session_id: str
    status: str = "active"
    target_role: str = ""
    company: str = ""
    cv_text: str = ""
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers: Dict[str, str] = Field(default_factory=dict)
    scores: Dict[str, AnswerScore] = Field(default_factory=dict)
    question_index: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class InterviewSessionManager:
    def __init__(self, max_sessions: int = 200) -> None:
        self._sessions: Dict[str, InterviewRecord] = {}
        self._lock = threading.Lock()
        self._max = max_sessions

    def create(self, session: InterviewRecord) -> InterviewRecord:
        with self._lock:
            if len(self._sessions) >= self._max and self._sessions:
                oldest = min(self._sessions.items(), key=lambda x: x[1].created_at)
                del self._sessions[oldest[0]]
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[InterviewRecord]:
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session: InterviewRecord) -> None:
        with self._lock:
            self._sessions[session.session_id] = session


_manager = InterviewSessionManager()


def get_interview_session_manager() -> InterviewSessionManager:
    return _manager
