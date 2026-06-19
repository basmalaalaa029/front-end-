"""Tests for CV router instant template + async enhancement flow."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from cv_agent.app.config import PipelineConfig
from cv_agent.app.api import create_app
from cv_generator.models.pipeline import PipelineResult
from cv_generator.models.cv_schema import CVData, Experience


@pytest.fixture
def client():
    app = create_app(PipelineConfig())
    return TestClient(app)


def _payload():
    return {
        "full_name": "Jane Doe",
        "target_role": "Engineer",
        "email": "jane@example.com",
        "skills": ["Python"],
        "experience": [
            {
                "job_title": "Developer",
                "company": "Acme",
                "start_date": "2020",
                "end_date": "2022",
                "bullets": ["Built APIs"],
            },
        ],
    }


def test_generate_returns_template_immediately(client):
    with patch(
        "cv_generator.api.router.run_enhancement_sync",
        return_value=PipelineResult(
            session_id="test",
            candidate_name="Jane Doe",
            target_role="Engineer",
            total_iterations=1,
            final_cv="# Jane Doe\nEnhanced",
            template_cv="# Jane Doe\nTemplate",
            final_scores=None,
            score_trajectory=[80.0],
            node_errors=[],
            jd_keywords=[],
        ),
    ):
        res = client.post("/generate", json=_payload())
    assert res.status_code == 202
    body = res.json()
    assert body["session_id"]
    assert body["template_cv"]
    assert "## Work Experience" in body["template_cv"]
    assert "Developer" in body["template_cv"]
    assert body["status"] == "running"


def test_legacy_flat_experiences_payload(client):
    payload = {
        "full_name": "John Smith",
        "target_role": "Developer",
        "skills": ["JavaScript"],
        "experiences": ["Frontend Dev · WebCo · 2020 — 2022\n- Built UI components"],
    }
    with patch("cv_generator.api.router.run_enhancement_sync") as mock_run:
        mock_run.return_value = PipelineResult(
            session_id="legacy",
            candidate_name="John Smith",
            target_role="Developer",
            total_iterations=0,
            final_cv="# John Smith",
            template_cv="# John Smith",
            final_scores=None,
            score_trajectory=[],
            node_errors=[],
            jd_keywords=[],
        )
        res = client.post("/generate", json=payload)
    assert res.status_code == 202
    cv_data = mock_run.call_args[0][0]
    assert isinstance(cv_data, CVData)
    assert cv_data.experience[0].job_title == "Frontend Dev"
