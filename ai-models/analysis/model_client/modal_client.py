"""HTTP client for Modal-hosted CV analysis (dedicated or legacy GPU judge)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from analysis.config import (
    LEGACY_GPU_JUDGE_API_KEY,
    LEGACY_GPU_JUDGE_URL,
    MODAL_ENDPOINT_URL,
    MODAL_MAX_NEW_TOKENS,
    MODAL_REQUEST_TIMEOUT,
)
from analysis.model_client.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    build_analysis_user_prompt,
    normalize_target_role,
)
from cv_agent.app.utils import parse_json_robust

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


def _call_legacy_gpu_judge(
    resume_text: str,
    max_new_tokens: int,
    target_role: str = "",
) -> Optional[dict]:
    base = LEGACY_GPU_JUDGE_URL.rstrip("/")
    url = f"{base}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if LEGACY_GPU_JUDGE_API_KEY:
        headers["Authorization"] = f"Bearer {LEGACY_GPU_JUDGE_API_KEY}"

    payload = json.dumps(
        {
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_analysis_user_prompt(resume_text, target_role),
                },
            ],
            "temperature": 0,
            "max_tokens": max_new_tokens,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=MODAL_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        log.warning("Legacy GPU judge returned HTTP %s: %s — %s", exc.code, exc.reason, detail)
        return None
    except urllib.error.URLError as exc:
        log.warning("Could not reach legacy GPU judge: %s", exc.reason)
        return None
    except Exception as exc:
        log.warning("Legacy GPU judge call failed: %s", exc)
        return None

    try:
        raw = (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError):
        log.warning("Legacy GPU judge returned unexpected response shape")
        return None

    parsed = parse_json_robust(raw)
    if not parsed:
        log.warning("Legacy GPU judge output could not be parsed as JSON")
        return None

    return {"raw": raw, "parsed": parsed}


def call_analysis_model(
    resume_text: str,
    max_new_tokens: int = MODAL_MAX_NEW_TOKENS,
    target_role: str = "",
) -> Optional[dict]:
    """Returns {"raw": "...", "parsed": {...}} on success, or None on failure."""
    if MODAL_ENDPOINT_URL:
        return _call_dedicated_endpoint(resume_text, max_new_tokens, target_role)

    if LEGACY_GPU_JUDGE_URL:
        log.info("Using legacy GPU judge at %s", LEGACY_GPU_JUDGE_URL)
        return _call_legacy_gpu_judge(resume_text, max_new_tokens, target_role)

    log.error(
        "No analysis endpoint configured — set MODAL_ENDPOINT_URL or CV_ANALYSIS_LLAMA_SERVER_URL in .env"
    )
    return None
