"""Shared llama.cpp inference backend (GGUF, CPU-optimized).

This is the fast CPU path. A quantized GGUF model (e.g. Q4_K_M) loads a 7B model
in ~4.5 GB RAM and runs at usable token rates on CPU, where the float32
``transformers`` path would overflow RAM and stall for hours.

The HF ``transformers`` path is kept for GPU deployments; see the runtime
modules in ``cv/`` and ``analysis/`` for the backend switch.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, Optional

from cv_agent.app.config import logger


class LlamaGenerator:
    """Thin wrapper around a ``llama_cpp.Llama`` instance.

    Exposes a single ``chat()`` method so the existing ``chat`` / ``phi3_chat`` /
    ``judge_chat`` helpers can treat it as a drop-in replacement for an HF
    pipeline without leaking llama.cpp specifics into the pipelines.
    """

    def __init__(
        self,
        model_path: str,
        *,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = 0,
        chat_format: Optional[str] = None,
        default_max_tokens: int = 1024,
    ) -> None:
        from llama_cpp import Llama

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"GGUF model not found at '{model_path}'. "
                "Run scripts/download_gguf.py (and scripts/convert_to_gguf.py on a "
                "GPU for fine-tuned models) to populate ai-models/models/gguf/."
            )

        self.model_path = model_path
        self.default_max_tokens = default_max_tokens
        threads = n_threads or (os.cpu_count() or 4)
        logger.info(
            "[llama] Loading GGUF %s (n_ctx=%d, threads=%d, gpu_layers=%d)",
            os.path.basename(model_path), n_ctx, threads, n_gpu_layers,
        )
        t0 = time.perf_counter()
        kwargs: Dict[str, Any] = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_threads": threads,
            "n_gpu_layers": n_gpu_layers,
            "verbose": False,
        }
        if chat_format:
            kwargs["chat_format"] = chat_format
        self._llm = Llama(**kwargs)
        logger.info(
            "[llama] Loaded %s in %.1fs",
            os.path.basename(model_path), time.perf_counter() - t0,
        )

    def chat(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Run a single chat completion using the GGUF model's built-in template."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        t0 = time.perf_counter()
        out = self._llm.create_chat_completion(
            messages=messages,
            temperature=0.7 if temperature is None else temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
        )
        text = (out["choices"][0]["message"]["content"] or "").strip()
        logger.info(
            "[llama] %s generated %d chars in %.1fs",
            os.path.basename(self.model_path), len(text), time.perf_counter() - t0,
        )
        return text


_INSTANCES: Dict[str, LlamaGenerator] = {}
_INSTANCES_LOCK = threading.Lock()


def get_llama_generator(
    model_path: str,
    *,
    n_ctx: int = 4096,
    n_gpu_layers: int = 0,
    chat_format: Optional[str] = None,
    default_max_tokens: int = 1024,
) -> LlamaGenerator:
    """Return a cached LlamaGenerator for ``model_path`` (one instance per file)."""
    gen = _INSTANCES.get(model_path)
    if gen is None:
        with _INSTANCES_LOCK:
            gen = _INSTANCES.get(model_path)
            if gen is None:
                gen = LlamaGenerator(
                    model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    chat_format=chat_format,
                    default_max_tokens=default_max_tokens,
                )
                _INSTANCES[model_path] = gen
    return gen
