"""HTTP client for Modal-hosted CV analysis."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from analysis.config import (
    MODAL_ENDPOINT_URL,
    MODAL_MAX_NEW_TOKENS,
    MODAL_REQUEST_TIMEOUT,
)
from analysis.model_client.prompts import normalize_target_role

log = logging.getLogger("analysis")


def _call_dedicated_endpoint(
    resume_text: str,
    max_new_tokens: int,
    target_role: str = "",
) -> Optional[dict]:
    payload: dict = {
        "resume_text": resume_text,
        "max_new_tokens": max_new_tokens,
    }
    role = normalize_target_role(target_role)
    if role:
        payload["target_role"] = role

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        MODAL_ENDPOINT_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=MODAL_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        log.warning("Analysis endpoint returned HTTP %s: %s", exc.code, exc.reason)
        return None
    except urllib.error.URLError as exc:
        log.warning("Could not reach analysis endpoint: %s", exc.reason)
        return None
    except Exception as exc:
        log.warning("Analysis endpoint call failed: %s", exc)
        return None

    if "error" in data:
        log.warning("Analysis endpoint returned an error: %s", data["error"])
        return None

    if not data.get("parsed"):
        log.warning("Analysis endpoint did not return parsable JSON")
        return None

    return data


def call_analysis_model(
    resume_text: str,
    max_new_tokens: int = MODAL_MAX_NEW_TOKENS,
    target_role: str = "",
) -> Optional[dict]:
    """Returns {"raw": "...", "parsed": {...}} on success, or None on failure."""
    if MODAL_ENDPOINT_URL:
        return _call_dedicated_endpoint(resume_text, max_new_tokens, target_role)

    log.error("No analysis endpoint configured — set MODAL_ENDPOINT_URL in .env")
    return None
