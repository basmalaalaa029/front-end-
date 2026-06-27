"""Smoke tests for career interview API route registration."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    os.environ.setdefault("CV_AGENT_AUTH_DISABLED", "true")
    os.environ.setdefault("JWT_SECRET", "test-secret")
    from cv_agent.app.api import create_app

    return TestClient(create_app())


def test_start_route_registered(client: TestClient):
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/start" in paths
    assert "post" in paths["/start"]


def test_answer_routes_registered(client: TestClient):
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/answer/text" in paths
    assert "/answer/audio" in paths
    assert "/answer/video" in paths


def test_session_routes_registered(client: TestClient):
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/session/{user_id}" in paths
    assert "/results/{user_id}" in paths


def test_recruiter_api_registered(client: TestClient):
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/recruiter/sessions" in paths


def test_legacy_root_redirects_to_frontend(client: TestClient):
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert "/dashboard/interview" in res.headers.get("location", "")
