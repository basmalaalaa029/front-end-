"""Tests for Gemini service with mocked API."""

import asyncio
from unittest.mock import MagicMock, patch

from cv_agent.app.config import PipelineConfig
from cv_generator.models.cv_schema import CVData, Experience
from cv_generator.services.gemini_service import enhance_cv_with_gemini, _parse_json_response


def test_parse_json_response_salvages_wrapped_json():
    raw = 'Here is JSON:\n{"summary": "Pro summary", "skills": ["Python"]}'
    data = _parse_json_response(raw)
    assert data["summary"] == "Pro summary"


def test_enhance_cv_with_gemini_success():
    cv = CVData(
        full_name="Jane",
        target_role="Engineer",
        skills=["Python"],
        experience=[
            Experience(
                job_title="Dev",
                company="Co",
                start_date="2020",
                end_date="2021",
                bullets=["worked on apis"],
            ),
        ],
    )
    mock_response = MagicMock()
    mock_response.text = (
        '{"summary": "Engineer with Python skills.", '
        '"skills": {"backend": ["Python"]}, '
        '"experience": [{"job_title": "Dev", "company": "Co", "start_date": "2020", '
        '"end_date": "2021", "bullets": ["Developed APIs"]}], "projects": []}'
    )
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    cfg = PipelineConfig()
    cfg.gemini_api_key = "test-key"

    with patch("cv_generator.services.gemini_service._get_model", return_value=mock_model):
        result = asyncio.run(enhance_cv_with_gemini(cv, cfg))

    assert result["status"] == "success"
    assert "Developed APIs" in result["data"]["experience"][0]["bullets"]


def test_enhance_cv_missing_api_key():
    cv = CVData(full_name="Jane", target_role="Eng", skills=["Py"], experience=[])
    cfg = PipelineConfig()
    cfg.gemini_api_key = ""
    result = asyncio.run(enhance_cv_with_gemini(cv, cfg))
    assert result["status"] == "error"
