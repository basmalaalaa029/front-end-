"""Central configuration for the CV analysis feature."""

import os

MODAL_ENDPOINT_URL = os.getenv("MODAL_ENDPOINT_URL", "").strip()

# POST to start inference; poll budget is separate (Modal returns 303 every ~150s while GPU runs).
MODAL_POST_TIMEOUT = int(os.getenv("MODAL_POST_TIMEOUT", "180"))
MODAL_POLL_TIMEOUT = int(os.getenv("MODAL_POLL_TIMEOUT", "1800"))
MODAL_REQUEST_TIMEOUT = int(os.getenv("MODAL_REQUEST_TIMEOUT", str(MODAL_POLL_TIMEOUT)))
MODAL_MAX_NEW_TOKENS = int(os.getenv("MODAL_MAX_NEW_TOKENS", os.getenv("JUDGE_MAX_TOKENS", "2200")))

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
    return bool(MODAL_ENDPOINT_URL)
