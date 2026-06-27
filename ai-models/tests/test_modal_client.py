"""Modal HTTP client — 303 redirect + poll handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from analysis.model_client import modal_client


def test_modal_303_redirect_polls_result_url():
    ok_body = {
        "raw": "{}",
        "parsed": {"overall_score": 80, "clarity_score": 80, "structure_score": 80,
                   "impact_score": 80, "skills_relevance_score": 80, "ats_readiness_score": 80,
                   "strengths": [], "weaknesses": [], "improvement_suggestions": [],
                   "rewrite_suggestions": []},
    }

    post_resp = MagicMock()
    post_resp.status_code = 303
    post_resp.headers = {
        "location": "https://example.modal.run/?__modal_function_call_id=fc-1",
    }

    mock_client = MagicMock()
    mock_client.post.return_value = post_resp
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False

    mock_fc = MagicMock()
    mock_fc.get.return_value = ok_body
    mock_function_call = MagicMock()
    mock_function_call.from_id.return_value = mock_fc

    with patch.object(modal_client, "MODAL_ENDPOINT_URL", "https://example.modal.run"):
        with patch("analysis.model_client.modal_client.httpx.Client", return_value=mock_client):
            with patch.dict("sys.modules", {"modal": MagicMock(FunctionCall=mock_function_call)}):
                result = modal_client.call_analysis_model("x" * 60)

    assert result == ok_body
    mock_function_call.from_id.assert_called_once_with("fc-1")
    mock_fc.get.assert_called_once()


def test_modal_poll_retries_on_303_then_succeeds_via_http_fallback():
    ok_body = {
        "raw": "{}",
        "parsed": {"overall_score": 80, "clarity_score": 80, "structure_score": 80,
                   "impact_score": 80, "skills_relevance_score": 80, "ats_readiness_score": 80,
                   "strengths": [], "weaknesses": [], "improvement_suggestions": [],
                   "rewrite_suggestions": []},
    }

    post_resp = MagicMock()
    post_resp.status_code = 303
    post_resp.headers = {
        "location": "https://example.modal.run/?__modal_function_call_id=fc-2",
    }

    pending = MagicMock()
    pending.status_code = 303
    pending.headers = {"location": "https://example.modal.run/?__modal_function_call_id=fc-2"}

    done = MagicMock()
    done.status_code = 200
    done.json.return_value = ok_body

    mock_client = MagicMock()
    mock_client.post.return_value = post_resp
    mock_client.get.side_effect = [pending, done]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False

    with patch.object(modal_client, "MODAL_ENDPOINT_URL", "https://example.modal.run"):
        with patch("analysis.model_client.modal_client.httpx.Client", return_value=mock_client):
            with patch("analysis.model_client.modal_client._poll_modal_function_call", return_value=None):
                with patch("analysis.model_client.modal_client.time.sleep"):
                    result = modal_client.call_analysis_model("x" * 60)

    assert result == ok_body
    assert mock_client.get.call_count == 2
