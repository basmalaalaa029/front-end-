"""Load ai-models/.env once (shared by main, scripts, and pydantic settings)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

_loaded = False

_API_KEY_VARS = ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "JWT_SECRET")


def sanitize_api_key(value: str) -> str:
    """Strip smart punctuation from pasted API keys (em/en dashes break HTTP headers)."""
    if not value:
        return ""
    cleaned = (
        value.strip()
        .replace("\ufeff", "")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
    )
    return cleaned.encode("ascii", "ignore").decode("ascii")


def _sanitize_env_api_keys() -> None:
    for name in _API_KEY_VARS:
        raw = os.environ.get(name)
        if not raw:
            continue
        cleaned = sanitize_api_key(raw)
        if cleaned != raw:
            os.environ[name] = cleaned


def groq_api_key_configured() -> bool:
    key = sanitize_api_key(os.environ.get("GROQ_API_KEY", ""))
    return key.startswith("gsk_") and len(key) > 20


def _prepend_vendor_ffmpeg_to_path() -> None:
    """Use bundled ffmpeg from vendor/ffmpeg-static (install via scripts/install_ffmpeg.sh)."""
    vend = ROOT / "vendor" / "ffmpeg-static"
    if not (vend / "ffmpeg").is_file():
        return
    bin_dir = str(vend)
    current = os.environ.get("PATH", "")
    if bin_dir not in current.split(os.pathsep):
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{current}"


def load_env(*, override: bool = False) -> Path:
    """Load ``ai-models/.env`` into ``os.environ``. Idempotent unless ``override=True``."""
    global _loaded
    if _loaded and not override:
        return ENV_PATH

    try:
        from dotenv import load_dotenv
    except ImportError:
        _prepend_vendor_ffmpeg_to_path()
        return ENV_PATH

    if ENV_PATH.is_file():
        load_dotenv(ENV_PATH, override=override)
        _sanitize_env_api_keys()
    _prepend_vendor_ffmpeg_to_path()
    _loaded = True
    return ENV_PATH
