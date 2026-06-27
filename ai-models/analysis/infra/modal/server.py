"""
Modal GPU deployment for CV analysis (fine-tuned Qwen ATS model).

Deploy (from ai-models/):
    pip install modal
    modal setup
    modal secret create cv-analysis-secrets HF_TOKEN=hf_xxx ...
    modal deploy analysis/infra/modal/server.py

Copy the printed HTTPS URL into ai-models/.env as MODAL_ENDPOINT_URL.
"""

from __future__ import annotations

import os
from pathlib import Path

import modal
from pydantic import BaseModel, Field

# ── paths bundled into the Modal image ───────────────────────────────────────
_MODAL_DIR = Path(__file__).resolve().parent
_MODEL_CLIENT_DIR = _MODAL_DIR.parent.parent / "model_client"

DEFAULT_BASE = "OsamaHayba/qwen-ats-merged-stage1"
DEFAULT_ADAPTER = "OsamaHayba/cv-analysis-final-stage2"

app = modal.App("cv-analysis")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.1",
        "transformers>=4.40",
        "peft>=0.10",
        "accelerate>=0.25",
        "bitsandbytes>=0.41",
        "sentencepiece>=0.1",
        "fastapi>=0.100",
        "json-repair>=0.30",
        "huggingface-hub>=0.20",
    )
    .add_local_dir(_MODEL_CLIENT_DIR, remote_path="/pkg/model_client")
    .add_local_file(_MODAL_DIR / "json_parse.py", remote_path="/pkg/json_parse.py")
)


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    max_new_tokens: int = Field(default=800, ge=64, le=2048)
    target_role: str = ""


@app.cls(
    gpu="A10G",
    timeout=600,
    scaledown_window=300,
    secrets=[modal.Secret.from_name("cv-analysis-secrets")],
    image=image,
)
@modal.concurrent(max_inputs=1)
class CvAnalysisModel:
    @modal.enter()
    def load(self) -> None:
        import sys

        sys.path.insert(0, "/pkg")
        from model_client.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_user_prompt
        from json_parse import parse_json_robust

        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self._build_prompt = build_analysis_user_prompt
        self._system_prompt = ANALYSIS_SYSTEM_PROMPT
        self._parse_json = parse_json_robust

        token = (
            os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGINGFACE_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )
        merged_id = os.environ.get("ANALYSIS_MERGED_MODEL_ID", "").strip()
        base_id = os.environ.get("ANALYSIS_BASE_MODEL_ID", DEFAULT_BASE).strip()
        adapter_id = os.environ.get("ANALYSIS_ADAPTER_MODEL_ID", DEFAULT_ADAPTER).strip()

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        model_id = merged_id or base_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=token, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(
            model_id,
            token=token,
            trust_remote_code=True,
            quantization_config=bnb,
            device_map="auto",
        )

        if merged_id:
            self.model = base
        else:
            self.model = PeftModel.from_pretrained(base, adapter_id, token=token)

        self.model.eval()

    def _generate(self, resume_text: str, max_new_tokens: int, target_role: str) -> dict:
        import torch

        user_content = self._build_prompt(resume_text, target_role)
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_content},
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt = f"{self._system_prompt}\n\n{user_content}"

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.0,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        parsed = self._parse_json(raw)
        if not parsed:
            return {"error": "Model output could not be parsed as JSON", "raw": raw, "parsed": None}
        return {"raw": raw, "parsed": parsed}

    @modal.fastapi_endpoint(method="POST")
    def analyze(self, payload: AnalyzeRequest) -> dict:
        try:
            return self._generate(
                payload.resume_text,
                payload.max_new_tokens,
                payload.target_role,
            )
        except Exception as exc:
            return {"error": str(exc), "parsed": None}
