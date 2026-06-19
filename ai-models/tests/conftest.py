"""Pytest shared fixtures."""

from __future__ import annotations

import os

# CV Agent auth is enforced in production; tests run without JWT unless opted in.
os.environ.setdefault("CV_AGENT_AUTH_DISABLED", "true")
