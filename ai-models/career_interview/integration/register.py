"""Bootstrap flat imports and register career interview routes on CV Agent."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import register_career_interview_routes  # noqa: E402


def register_career_interview(app) -> None:
    register_career_interview_routes(app)
