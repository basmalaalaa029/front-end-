"""
gpu_inference/service.py
========================
OpenAI-compatible HTTP server for the fine-tuned Qwen ATS judge.

Run on a GPU machine (Modal, Colab tunnel, RunPod, etc.). Your CPU app points
``CV_ANALYSIS_INFERENCE_MODE=remote`` and ``CV_ANALYSIS_LLAMA_SERVER_URL`` here.

Usage (on GPU box, from ai-models/):
    export HUGGINGFACE_TOKEN=hf_...
    export GPU_INFERENCE_API_KEY=your-secret   # optional but recommended
    python -m uvicorn gpu_inference.service:app --host 0.0.0.0 --port 8080

Env:
    JUDGE_BASE_MODEL      default OsamaHayba/qwen-ats-merged-stage1
    JUDGE_ADAPTER_PATH    default OsamaHayba/cv-analysis-final-stage2
    HUGGINGFACE_TOKEN     HF hub token (private/gated models)
    GPU_INFERENCE_API_KEY Bearer token clients must send (optional)
    GPU_INFERENCE_PORT    default 8080
    LOAD_IN_4BIT          default true — 4-bit base (~8 GB VRAM)
    GPU_INFERENCE_MAX_NEW_TOKENS  default 1200
"""

from __future__ import annotations

import os
import threading
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# ── Config from env ───────────────────────────────────────────────────────────

BASE_MODEL = os.getenv("JUDGE_BASE_MODEL", "OsamaHayba/qwen-ats-merged-stage1")
ADAPTER_PATH = os.getenv("JUDGE_ADAPTER_PATH", "OsamaHayba/cv-analysis-final-stage2")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or None
API_KEY = (os.getenv("GPU_INFERENCE_API_KEY") or "").strip()
LOAD_IN_4BIT = os.getenv("LOAD_IN_4BIT", "true").lower() in ("1", "true", "yes")
MAX_NEW_TOKENS = int(os.getenv("GPU_INFERENCE_MAX_NEW_TOKENS", "1200"))

# ── Model state (loaded once at startup) ──────────────────────────────────────

_model: Any = None
_tokenizer: Any = None
_load_error: Optional[str] = None
_load_lock = threading.Lock()


def _load_model() -> None:
    global _model, _tokenizer, _load_error
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"[gpu_inference] Loading base: {BASE_MODEL}")
        tok_kw: dict[str, Any] = {"trust_remote_code": True}
        if HF_TOKEN:
            tok_kw["token"] = HF_TOKEN

        _tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, **tok_kw)

        model_kw: dict[str, Any] = {
            "trust_remote_code": True,
            "device_map": {"": 0},
        }
        if HF_TOKEN:
            model_kw["token"] = HF_TOKEN

        if LOAD_IN_4BIT:
            from transformers import BitsAndBytesConfig

            model_kw["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        else:
            model_kw["torch_dtype"] = torch.float16

        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, **model_kw)
        print(f"[gpu_inference] Applying LoRA: {ADAPTER_PATH}")
        adapter_kw: dict[str, Any] = {}
        if HF_TOKEN:
            adapter_kw["token"] = HF_TOKEN
        _model = PeftModel.from_pretrained(model, ADAPTER_PATH, **adapter_kw)
        _model.eval()
        print("[gpu_inference] Model ready.")
    except Exception as exc:
        _load_error = str(exc)
        print(f"[gpu_inference] Load failed: {exc}")
        raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    thread = threading.Thread(target=_load_model, name="gpu-model-load", daemon=True)
    thread.start()
    thread.join(timeout=600)
    if thread.is_alive():
        print("[gpu_inference] Model still loading in background…")
    yield


app = FastAPI(title="CV Analysis GPU Judge", version="1.0", lifespan=lifespan)


def _check_api_key(request: Request) -> None:
    if not API_KEY:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _model_ready() -> bool:
    return _model is not None and _tokenizer is not None


@app.get("/health")
def health() -> dict[str, Any]:
    if _load_error:
        return {"status": "error", "error": _load_error}
    if not _model_ready():
        return {"status": "loading", "model_loaded": False}
    return {"status": "ok", "model_loaded": True, "base": BASE_MODEL, "adapter": ADAPTER_PATH}


@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    return {"data": [{"id": "cv-analysis-judge", "object": "model"}]}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.1
    max_tokens: int = Field(default=MAX_NEW_TOKENS, ge=1, le=4096)


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest, request: Request) -> dict[str, Any]:
    _check_api_key(request)

    if _load_error:
        raise HTTPException(status_code=503, detail=f"Model load failed: {_load_error}")
    if not _model_ready():
        raise HTTPException(status_code=503, detail="Model still loading")

    import torch

    system = next((m.content for m in req.messages if m.role == "system"), "")
    user = next((m.content for m in req.messages if m.role == "user"), "")
    if not user:
        raise HTTPException(status_code=400, detail="Missing user message")

    chat_messages = []
    if system:
        chat_messages.append({"role": "system", "content": system})
    chat_messages.append({"role": "user", "content": user})

    text = _tokenizer.apply_chat_template(
        chat_messages, tokenize=False, add_generation_prompt=True,
    )
    inputs = _tokenizer([text], return_tensors="pt").to(_model.device)

    t0 = time.perf_counter()
    with torch.no_grad():
        out = _model.generate(
            inputs.input_ids,
            max_new_tokens=req.max_tokens,
            do_sample=req.temperature > 0,
            temperature=req.temperature if req.temperature > 0 else None,
            repetition_penalty=1.1,
            eos_token_id=_tokenizer.eos_token_id,
            pad_token_id=_tokenizer.eos_token_id,
        )

    new_ids = out[0][inputs.input_ids.shape[1]:]
    content = _tokenizer.decode(new_ids, skip_special_tokens=True).strip()
    elapsed = time.perf_counter() - t0
    print(f"[gpu_inference] Generated {len(content)} chars in {elapsed:.1f}s")

    return {
        "id": "chatcmpl-gpu",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
        "usage": {"completion_tokens": len(new_ids), "prompt_tokens": inputs.input_ids.shape[1]},
    }
