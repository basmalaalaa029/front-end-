"""Tests for the analysis feature HTTP API."""

from __future__ import annotations

import io
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from cv_agent.app.api import create_app

SAMPLE_MODEL_RESPONSE = {
    "raw": "{}",
    "parsed": {
        "clarity_score": 80,
        "structure_score": 75,
        "impact_score": 70,
        "skills_relevance_score": 72,
        "ats_readiness_score": 78,
        "overall_score": 75,
        "strengths": ["Clear experience section", "Strong technical skills"],
        "issues": [
            {
                "issue": "Missing metrics in bullets",
                "whats_wrong": "Experience bullets describe tasks without quantified outcomes.",
                "what_to_do": "Add quantified outcomes where numbers already exist in the resume.",
                "example": "Built REST APIs for the payments platform.",
            },
            {
                "issue": "Summary too generic",
                "whats_wrong": "The professional summary does not mention a target role or specialty.",
                "what_to_do": "Tailor the summary to the target role with your strongest relevant skills.",
                "example": "Software engineer with backend and API experience.",
            },
        ],
    },
}

INVALID_MODEL_RESPONSE = {
    "raw": "{}",
    "parsed": {
        "clarity_score": 80,
        "structure_score": 75,
        "impact_score": 70,
        "skills_relevance_score": 72,
        "ats_readiness_score": 78,
        "overall_score": 75,
        "strengths": ["Clear experience section"],
        "issues": [],
    },
}


def _poll_until_terminal(client, job_id: str, *, timeout_s: float = 10.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        poll = client.get(f"/cv-analysis/analyze/{job_id}")
        assert poll.status_code == 200
        data = poll.json()
        if data["status"] in ("ready", "failed"):
            return data
        time.sleep(0.1)
    pytest.fail("timed out waiting for terminal analysis status")


def _minimal_pdf() -> bytes:
  """Tiny valid PDF with extractable text."""
  return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Senior Software Engineer experience Python FastAPI) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000052 00000 n 
0000000101 00000 n 
0000000206 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
300
%%EOF"""


@pytest.fixture
def client():
    return TestClient(create_app())


def test_analysis_upload_and_poll(client):
    captured: dict = {}

    def _fake_call(resume_text: str, max_new_tokens: int = 800, target_role: str = ""):
        captured["resume_text"] = resume_text
        captured["target_role"] = target_role
        return SAMPLE_MODEL_RESPONSE

    with patch("analysis.model_client.modal_client.call_analysis_model", side_effect=_fake_call):
        files = {"file": ("resume.pdf", io.BytesIO(_minimal_pdf()), "application/pdf")}
        data = {"target_role": "Full Stack Developer"}
        start = client.post("/cv-analysis/analyze", files=files, data=data)
        assert start.status_code == 200
        body = start.json()
        assert body["status"] == "processing"
        job_id = body["job_id"]
        assert job_id

        final = _poll_until_terminal(client, job_id)
        assert final["status"] == "ready"
        assert final["stage"] == "done"
        result = final["result"]
        assert result["overall_score"] == 75
        assert len(result["strengths"]) >= 1
        assert len(result["issues"]) >= 2
        assert "ats" not in result and "hr" not in result
        assert captured.get("target_role") == "Full Stack Developer"


def test_analysis_unknown_job_returns_404(client):
    resp = client.get("/cv-analysis/analyze/doesnotexist")
    assert resp.status_code == 404


def test_analysis_model_unreachable_marks_failed(client):
    with patch("analysis.model_client.modal_client.call_analysis_model", return_value=None):
        text = "A" * 60
        files = {"file": ("cv.txt", io.BytesIO(text.encode()), "text/plain")}
        start = client.post("/cv-analysis/analyze", files=files)
        assert start.status_code == 200
        job_id = start.json()["job_id"]

        data = _poll_until_terminal(client, job_id)
        assert data["status"] == "failed"
        assert data["error"]


def test_analysis_validation_failure_marks_failed(client):
    with patch(
        "analysis.model_client.modal_client.call_analysis_model",
        return_value=INVALID_MODEL_RESPONSE,
    ):
        text = "A" * 60
        files = {"file": ("cv.txt", io.BytesIO(text.encode()), "text/plain")}
        start = client.post("/cv-analysis/analyze", files=files)
        assert start.status_code == 200
        job_id = start.json()["job_id"]

        data = _poll_until_terminal(client, job_id)
        assert data["status"] == "failed"
        assert "incomplete response" in data["error"].lower()
