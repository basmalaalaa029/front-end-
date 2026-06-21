"""CV analysis async job API flow."""

from __future__ import annotations

from unittest.mock import patch

import httpx

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
    assert "ats" in result
    assert "hr" in result
    assert result["ats"]["overall_score"] >= 0
    assert "cv_inventory" not in result
    assert "analysis" not in result


def test_target_role_reaches_judge_prompt(monkeypatch):
    monkeypatch.setenv("CV_ANALYSIS_MOCK_INFERENCE", "true")
    from cv_analysis.config import reset_config_cache
    reset_config_cache()

    from cv_analysis.judges.cache import get_cache
    from cv_analysis.judges.model_runtime import get_analysis_runtime
    from cv_analysis.judges.queue import inference_queue
    from cv_analysis.pipeline import run_analysis_pipeline

    get_cache().clear()
    runtime = get_analysis_runtime()
    runtime.start()
    inference_queue.mark_ready()
    inference_queue.start()

    prompts: list[str] = []

    def _capture_chat(_pipe, system, user, temperature=None):
        prompts.append(user)
        from cv_analysis.judges.model_runtime import MockLlamaClient
        return MockLlamaClient().chat(system, user)

    monkeypatch.setattr("cv_analysis.judges.llm_analysis.judge_chat", _capture_chat)

    run_analysis_pipeline(cv_text=SAMPLE_CV, target_role="Data Scientist")
    assert prompts
    assert "Target role: Data Scientist" in prompts[0]

    prompts.clear()
    get_cache().clear()
    run_analysis_pipeline(cv_text=SAMPLE_CV, target_role="Product Manager")
    assert prompts
    assert "Target role: Product Manager" in prompts[0]


def test_remote_inference_connects_without_local_gguf(monkeypatch):
    """Remote mode skips local llama-server and uses HTTP client only."""
    monkeypatch.setenv("CV_ANALYSIS_INFERENCE_MODE", "remote")
    monkeypatch.setenv("CV_ANALYSIS_LLAMA_SERVER_URL", "http://remote-gpu.test:8080")
    monkeypatch.setenv("CV_ANALYSIS_REMOTE_API_KEY", "test-key")
    from cv_analysis.config import reset_config_cache
    reset_config_cache()

    import cv_analysis.judges.model_runtime as rt
    rt._runtime = None

    health_resp = httpx.Response(
        200,
        json={"status": "ok", "model_loaded": True},
        request=httpx.Request("GET", "http://remote-gpu.test:8080/health"),
    )

    with patch.object(rt, "httpx") as mock_httpx:
        mock_client = mock_httpx.Client.return_value.__enter__.return_value
        mock_client.get.return_value = health_resp

        runtime = rt.get_analysis_runtime()
        runtime.start()

    assert runtime.ready
    assert runtime.client is not None
    mock_client.get.assert_called()


def test_judge_cache_varies_by_target_role():
    from cv_analysis.judges.cache import LRUCache
    from cv_analysis.judges.utils import jd_hash
    from hashlib import md5

    cv_hash = md5(b"cv").hexdigest()[:12]
    key_a = LRUCache.make_key(cv_hash, jd_hash("Data Scientist|"), 0, "combined-judge", namespace="judge")
    key_b = LRUCache.make_key(cv_hash, jd_hash("Product Manager|"), 0, "combined-judge", namespace="judge")
    assert key_a != key_b
