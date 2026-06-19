"""Tests for wizard /generate-ai-cv endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from cv_agent.app.api import create_app
from cv_agent.app.config import PipelineConfig


@pytest.fixture
def client():
    return TestClient(create_app(PipelineConfig()))


def _wizard_payload():
    return {
        "full_name": "Jane Doe",
        "target_job": "Full Stack Developer",
        "email": "jane@example.com",
        "education": [
            {
                "degree": "BSc Computer Science",
                "university": "State University",
                "year": "2026",
            },
        ],
        "experience": [
            {
                "job_title": "Intern",
                "company": "Acme",
                "start_date": "2025",
                "end_date": "2026",
                "description": "worked on APIs, fixed bugs",
            },
        ],
        "has_experience": True,
    }


def test_generate_ai_cv_success(client):
    fake_cv = {
        "personal_info": {"full_name": "Jane Doe", "email": "jane@example.com"},
        "summary": "Full Stack Developer intern.",
        "skills": {"backend": ["Node.js"]},
        "experience": [],
        "education": [],
    }
    with patch(
        "cv_generator.api.router.generate_cv_from_info",
        new_callable=AsyncMock,
        return_value={"status": "success", "cv": fake_cv},
    ):
        res = client.post("/generate-ai-cv", json=_wizard_payload())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["cv"]["target_title"] == "Full Stack Developer"
    assert body["cv"]["personal_info"]["full_name"] == "Jane Doe"


def test_wizard_to_cv_data_maps_description_to_bullets():
    from cv_generator.models.cv_schema import WizardStep1Request

    req = WizardStep1Request(**_wizard_payload())
    cv = req.to_cv_data()
    assert cv.full_name == "Jane Doe"
    assert cv.target_role == "Full Stack Developer"
    assert cv.skills == []
    assert cv.experience[0].bullets == ["worked on APIs, fixed bugs"]
