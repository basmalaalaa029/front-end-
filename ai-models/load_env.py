"""Load ai-models/.env once (shared by main, scripts, and pydantic settings)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

_loaded = False


def load_env(*, override: bool = False) -> Path:
    """Load ``ai-models/.env`` into ``os.environ``. Idempotent unless ``override=True``."""
    global _loaded
    if _loaded and not override:
        return ENV_PATH

    try:
        from dotenv import load_dotenv
    except ImportError:
        return ENV_PATH

    if ENV_PATH.is_file():
        load_dotenv(ENV_PATH, override=override)
        _loaded = True
    return ENV_PATH
