"""CV analysis async job API flow."""

from __future__ import annotations

from unittest.mock import patch

from cv_analysis.api.service import get_job_status, start_analysis_job
from cv_analysis.config import CVAnalysisConfig


SAMPLE_CV = """
# Jane Doe
jane@example.com | +1 555 0100

## Summary
Backend engineer with 5 years building APIs.

## Skills
Python, FastAPI, PostgreSQL, Docker

## Experience
### Senior Engineer — Acme Corp (2020–2024)
- Built payment APIs serving 2M users
- Reduced latency 40% with caching layer

## Education
### BSc Computer Science — MIT (2016–2020)
"""

MOCK_RESULT = {
    "cv_inventory": "Jane Doe — Backend engineer",
    "ats_signals": "ATS SIGNALS",
    "keyword_coverage": {"coverage": [], "missing_keywords": [], "jd_keywords": []},
    "analysis": {
        "ats": {"overall_score": 75, "clarity_score": 75, "structure_score": 75,
                "impact_score": 75, "skills_relevance_score": 75, "ats_readiness_score": 75,
                "strengths": [], "weaknesses": [], "improvement_suggestions": [], "rewrite_suggestions": []},
        "hr": {"overall_score": 76, "clarity_score": 76, "structure_score": 76,
               "impact_score": 76, "skills_relevance_score": 76, "ats_readiness_score": 76,
               "strengths": [], "weaknesses": [], "improvement_suggestions": [], "rewrite_suggestions": []},
        "blended": {"overall_score": 75, "clarity_score": 75, "structure_score": 75,
                    "impact_score": 75, "skills_relevance_score": 75, "ats_readiness_score": 75,
                    "strengths": [], "weaknesses": [], "improvement_suggestions": [], "rewrite_suggestions": []},
    },
    "latency_ms": 100,
}


def test_start_analysis_job_returns_job_id():
    cfg = CVAnalysisConfig(mock_inference=True)
    with patch("cv_analysis.api.service._run_job_background"):
        resp = start_analysis_job(cv_text=SAMPLE_CV, jd_text="Python FastAPI backend role", cfg=cfg)
    assert resp.job_id
    assert resp.status == "processing"


def test_get_job_status_processing():
    cfg = CVAnalysisConfig(mock_inference=True)
    with patch("cv_analysis.api.service._run_job_background"):
        resp = start_analysis_job(cv_text=SAMPLE_CV, cfg=cfg)
    status = get_job_status(resp.job_id)
    assert status is not None
    assert status.status == "processing"
    assert status.stage in ("parsing", "features", "judging", "done")


def test_pipeline_mock_inference(monkeypatch):
    monkeypatch.setenv("CV_ANALYSIS_MOCK_INFERENCE", "true")
    from cv_analysis.config import reset_config_cache
    reset_config_cache()

    from cv_analysis.judges.model_runtime import get_analysis_runtime
    from cv_analysis.judges.queue import inference_queue

    runtime = get_analysis_runtime()
    runtime.start()
    inference_queue.mark_ready()
    inference_queue.start()

    from cv_analysis.pipeline import run_analysis_pipeline
    result = run_analysis_pipeline(cv_text=SAMPLE_CV)
    assert "analysis" in result
    assert result["analysis"]["ats"]["overall_score"] >= 0
