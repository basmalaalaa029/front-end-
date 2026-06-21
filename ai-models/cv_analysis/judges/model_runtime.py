"""CV analysis judge runtime — llama-server subprocess + OpenAI-compatible HTTP client."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, List, Optional

import httpx

from cv_agent.app.config import logger
from cv_analysis.config import CVAnalysisConfig, get_cv_analysis_config


class LlamaCppClient:
    """HTTP client for llama-server /v1/chat/completions (local or remote GPU)."""

    def __init__(self, base_url: str, *, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key = (api_key or "").strip()

    def _headers(self) -> dict[str, str]:
        if self._api_key:
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        url = f"{self.base_url}/v1/chat/completions"
        t0 = time.perf_counter()
        with httpx.Client(timeout=None) as client:
            resp = client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        text = (data["choices"][0]["message"]["content"] or "").strip()
        logger.info(
            "[cv_analysis] inference server generated %d chars in %.1fs",
            len(text), time.perf_counter() - t0,
        )
        return text


class MockLlamaClient:
    """Deterministic mock for tests — returns minimal combined judge JSON."""

    def chat(self, system: str, user: str, *, temperature: float = 0.1, max_tokens: int = 1200) -> str:
        del system, user, temperature, max_tokens
        return (
            '{"ats":{"clarity_score":75,"structure_score":80,"impact_score":70,'
            '"skills_relevance_score":72,"ats_readiness_score":78,"overall_score":75,'
            '"strengths":["Clear structure"],"weaknesses":["Add more metrics"],'
            '"improvement_suggestions":["Quantify achievements"],'
            '"rewrite_suggestions":["Increased revenue by 20%"]},'
            '"hr":{"clarity_score":76,"structure_score":79,"impact_score":71,'
            '"skills_relevance_score":74,"ats_readiness_score":77,"overall_score":76,'
            '"strengths":["Relevant experience"],"weaknesses":["Summary could be stronger"],'
            '"improvement_suggestions":["Lead with role fit"],'
            '"rewrite_suggestions":["Senior engineer with 5 years…"]}}'
        )


class LlamaServerProcess:
    """Manages llama-server subprocess lifecycle."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._ready = False
        self._client: Any = None

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def client(self) -> Any:
        if self._client is None:
            raise RuntimeError("CV analysis judge runtime not started")
        return self._client

    def start(self, cfg: Optional[CVAnalysisConfig] = None) -> None:
        cfg = cfg or get_cv_analysis_config()
        with self._lock:
            if self._ready:
                return

            if cfg.mock_inference:
                self._client = MockLlamaClient()
                self._ready = True
                logger.info("[cv_analysis] Using mock inference client")
                return

            if cfg.is_remote_inference():
                base_url = cfg.resolve_inference_url()
                timeout_s = cfg.remote_health_timeout_s
                logger.info(
                    "[cv_analysis] Remote inference mode — connecting to %s (timeout %ds)",
                    base_url, timeout_s,
                )
                if self._wait_for_health(base_url, timeout_s=timeout_s, proc=None):
                    self._client = LlamaCppClient(base_url, api_key=cfg.remote_api_key)
                    self._ready = True
                    logger.info("[cv_analysis] Remote judge server ready at %s", base_url)
                else:
                    logger.error(
                        "[cv_analysis] Remote judge server not reachable at %s — "
                        "start gpu_inference on GPU: ./scripts/run_gpu_inference.sh",
                        base_url,
                    )
                return

            model_path = cfg.resolve_model_path()
            if not os.path.exists(model_path):
                logger.warning(
                    "[cv_analysis] GGUF not found at %s — run: python scripts/download_gguf.py",
                    model_path,
                )
                return

            port = cfg.llama_server_port
            base_url = cfg.llama_server_url or f"http://127.0.0.1:{port}"
            bin_path = cfg.resolve_llama_server_bin()

            if bin_path and os.path.isfile(bin_path):
                cmd = [
                    bin_path,
                    "-m", model_path,
                    "--port", str(port),
                    "-ngl", str(cfg.model_gpu_layers),
                    "-c", str(cfg.model_ctx_size),
                    "-t", str(cfg.model_threads),
                ]
                logger.info("[cv_analysis] Starting llama-server: %s", " ".join(cmd))
            elif shutil.which(bin_path or ""):
                cmd = [
                    bin_path,
                    "-m", model_path,
                    "--port", str(port),
                    "-ngl", str(cfg.model_gpu_layers),
                    "-c", str(cfg.model_ctx_size),
                    "-t", str(cfg.model_threads),
                ]
                logger.info("[cv_analysis] Starting llama-server: %s", " ".join(cmd))
            else:
                logger.warning(
                    "[cv_analysis] Native llama-server not found at %s — using llama_cpp.server fallback. "
                    "For production, run: ./scripts/install_llama_server.sh",
                    bin_path,
                )
                cmd = [
                    sys.executable, "-m", "llama_cpp.server",
                    "--model", model_path,
                    "--host", "127.0.0.1",
                    "--port", str(port),
                    "--n_gpu_layers", str(cfg.model_gpu_layers),
                    "--n_ctx", str(cfg.model_ctx_size),
                    "--n_threads", str(cfg.model_threads),
                ]
                logger.info("[cv_analysis] Starting llama_cpp.server: %s", " ".join(cmd))

            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            )
            if self._wait_for_health(base_url, timeout_s=180, proc=self._proc):
                self._client = LlamaCppClient(base_url, api_key=cfg.remote_api_key)
                self._ready = True
                logger.info("[cv_analysis] Judge server ready at %s", base_url)
            else:
                err = ""
                if self._proc and self._proc.stderr:
                    try:
                        err = self._proc.stderr.read(2000).decode(errors="replace")
                    except Exception:
                        pass
                self._stop_proc()
                logger.error(
                    "[cv_analysis] Judge server failed to become ready%s",
                    f": {err[:500]}" if err else "",
                )

    def _wait_for_health(
        self, base_url: str, timeout_s: int = 120, proc: Optional[subprocess.Popen] = None,
    ) -> bool:
        deadline = time.monotonic() + timeout_s
        probes: List[str] = [
            f"{base_url.rstrip('/')}/health",
            f"{base_url.rstrip('/')}/v1/models",
            f"{base_url.rstrip('/')}/docs",
        ]
        while time.monotonic() < deadline:
            if proc is not None and proc.poll() is not None:
                return False
            for health_url in probes:
                try:
                    with httpx.Client(timeout=5.0) as client:
                        resp = client.get(health_url)
                        if resp.status_code == 200:
                            # Remote GPU service may still be loading weights.
                            try:
                                body = resp.json()
                                if body.get("status") == "loading":
                                    continue
                                if body.get("status") == "error":
                                    logger.error(
                                        "[cv_analysis] Remote server error: %s",
                                        body.get("error", body),
                                    )
                                    return False
                            except Exception:
                                pass
                            return True
                except Exception:
                    pass
            time.sleep(2.0)
        return False

    def stop(self) -> None:
        with self._lock:
            self._stop_proc()
            self._client = None
            self._ready = False

    def _stop_proc(self) -> None:
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            self._proc.wait(timeout=10)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None


_runtime: Optional[LlamaServerProcess] = None
_runtime_lock = threading.Lock()


def get_analysis_runtime() -> LlamaServerProcess:
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                _runtime = LlamaServerProcess()
    return _runtime


def judge_chat(_pipe: Any, system: str, user: str, temperature: Optional[float] = None) -> str:
    """Drop-in judge chat — ``_pipe`` is ignored; uses llama-server client."""
    cfg = get_cv_analysis_config()
    client = get_analysis_runtime().client
    return client.chat(
        system, user,
        temperature=0.1 if temperature is None else temperature,
        max_tokens=cfg.judge_max_tokens,
    )
