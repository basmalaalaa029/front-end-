"""CV analysis configuration — pydantic-settings with CV_ANALYSIS_* env prefix."""

from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PKG_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PKG_ROOT / ".env"


class CVAnalysisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CV_ANALYSIS_",
        env_file=str(_ENV_FILE),
        extra="ignore",
    )

    model_repo: str = "basmalaalaa029/cv-analysis-gguf"
    model_file: str = "cv-analysis-Q4_K_M.gguf"
    model_ctx_size: int = 8192
    model_gpu_layers: int = 0
    model_threads: int = Field(default_factory=lambda: os.cpu_count() or 4)

    # local  -> start llama-server subprocess with GGUF on this machine
    # remote -> connect to an external OpenAI-compatible server (gpu_inference/service.py)
    inference_mode: str = Field(
        default_factory=lambda: os.getenv("CV_ANALYSIS_INFERENCE_MODE", "local").lower()
    )
    inference_backend: str = "llama_cpp"
    llama_server_url: str = "http://127.0.0.1:8080"
    llama_server_port: int = 8080
    llama_server_bin: str = "llama-server"
    remote_api_key: str = Field(default_factory=lambda: os.getenv("CV_ANALYSIS_REMOTE_API_KEY", ""))
    remote_health_timeout_s: int = Field(
        default_factory=lambda: int(os.getenv("CV_ANALYSIS_REMOTE_HEALTH_TIMEOUT_S", "300"))
    )
    gguf_dir: str = Field(default_factory=lambda: os.getenv("GGUF_DIR", "models/gguf"))

    max_concurrent_inferences: int = 1
    judge_max_tokens: int = 1200
    judge_max_retries: int = 3

    job_ttl_seconds: int = 3600
    job_max_sessions: int = 200

    ontology_path: str = Field(default_factory=lambda: os.getenv("ONTOLOGY_PATH", ""))
    embedding_model: str = "all-MiniLM-L6-v2"

    cache_ttl_seconds: int = 3600
    cache_max_size: int = 256

    warmup_on_startup: bool = True
    mock_inference: bool = False

    hf_token: str = Field(default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", ""))
    allow_model_download: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_MODEL_DOWNLOAD", "false").lower() in ("1", "true", "yes")
    )

    def resolve_model_path(self) -> str:
        path = self.model_file
        if os.path.isabs(path):
            return path
        gguf = self.gguf_dir
        if not os.path.isabs(gguf):
            # Resolve relative to ai-models root (parent of cv_analysis package).
            pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gguf = os.path.join(pkg_root, gguf)
        return os.path.join(gguf, path)

    def is_remote_inference(self) -> bool:
        return (self.inference_mode or "local").lower() == "remote"

    def resolve_inference_url(self) -> str:
        if self.llama_server_url:
            return self.llama_server_url.rstrip("/")
        return f"http://127.0.0.1:{self.llama_server_port}"

    def resolve_llama_server_bin(self) -> str:
        """Return path to llama-server: explicit config → repo bin/ → PATH."""
        pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if self.llama_server_bin:
            if os.path.isabs(self.llama_server_bin) and os.path.isfile(self.llama_server_bin):
                return self.llama_server_bin
            rel = os.path.join(pkg_root, self.llama_server_bin)
            if os.path.isfile(rel):
                return rel
            if os.path.isfile(self.llama_server_bin):
                return self.llama_server_bin
        bundled = os.path.join(pkg_root, "bin", "llama-server")
        if os.path.isfile(bundled):
            return bundled
        found = shutil.which("llama-server")
        return found or (self.llama_server_bin or "llama-server")


@lru_cache(maxsize=1)
def get_cv_analysis_config() -> CVAnalysisConfig:
    return CVAnalysisConfig()


def reset_config_cache() -> None:
    get_cv_analysis_config.cache_clear()
