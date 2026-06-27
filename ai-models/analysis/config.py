"""Central configuration for the CV analysis feature."""

import os

MODAL_ENDPOINT_URL = os.getenv("MODAL_ENDPOINT_URL", "").strip()

# Legacy Modal GPU judge (OpenAI-compatible /v1/chat/completions) — used when
# MODAL_ENDPOINT_URL is unset but CV_ANALYSIS_LLAMA_SERVER_URL is still in .env.
LEGACY_GPU_JUDGE_URL = os.getenv("CV_ANALYSIS_LLAMA_SERVER_URL", "").strip()
LEGACY_GPU_JUDGE_API_KEY = os.getenv("CV_ANALYSIS_REMOTE_API_KEY", "").strip()

MODAL_REQUEST_TIMEOUT = int(os.getenv("MODAL_REQUEST_TIMEOUT", os.getenv("CV_ANALYSIS_REMOTE_HEALTH_TIMEOUT_S", "120")))
MODAL_MAX_NEW_TOKENS = int(os.getenv("MODAL_MAX_NEW_TOKENS", os.getenv("JUDGE_MAX_TOKENS", "800")))

ANALYSIS_BASE_MODEL_ID = "OsamaHayba/qwen-ats-merged-stage1"
ANALYSIS_ADAPTER_MODEL_ID = "OsamaHayba/cv-analysis-final-stage2"
ANALYSIS_SCHEMA_VERSION = "stage2_v1"

ALLOWED_UPLOAD_EXTENSIONS = (".pdf", ".docx", ".txt")
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MIN_EXTRACTED_TEXT_CHARS = 200

SESSION_MAX_SESSIONS = int(os.getenv("ANALYSIS_SESSION_MAX", "500"))
SESSION_TTL_SECONDS = int(os.getenv("ANALYSIS_SESSION_TTL_SECONDS", "3600"))

SCORE_MIN = 0
SCORE_MAX = 100


def analysis_endpoint_configured() -> bool:
    return bool(MODAL_ENDPOINT_URL or LEGACY_GPU_JUDGE_URL)
