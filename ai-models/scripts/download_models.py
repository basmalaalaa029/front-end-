"""
scripts/download_models.py
==========================
Pre-download all HuggingFace models to the local cache.

Run this ONCE before starting the server so the first request
doesn't time out waiting for downloads.

Usage:
    python scripts/download_models.py
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from load_env import load_env
from huggingface_hub import snapshot_download

load_env()

TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
PHI3_ADAPTER_SUBFOLDER = os.getenv("PHI3_ADAPTER_SUBFOLDER", "checkpoint-200")
if not TOKEN:
    print("WARNING: HUGGINGFACE_TOKEN not set in .env — some models may require it.")

USE_MISTRAL_WRITER = os.getenv("USE_MISTRAL_WRITER", "false").lower() == "true"

MODELS = [
    # cv/ generation feature
    ("Phi-3 base",                  os.getenv("PHI3_BASE_MODEL", "microsoft/Phi-3-mini-4k-instruct")),
    ("Phi-3 CV LoRA adapter",       os.getenv("PHI3_MODEL", "basmalaalaa029/phi3-cv")),
    # analysis/ feature
    ("ATS Judge base (Qwen)",       "OsamaHayba/qwen-ats-merged-stage1"),
    ("ATS Judge adapter",           "OsamaHayba/cv-analysis-final-stage2"),
    ("HR Judge (Qwen2.5-7B)",       "Qwen/Qwen2.5-7B-Instruct"),
    ("Embedding (MiniLM-L6)",       "sentence-transformers/all-MiniLM-L6-v2"),
]

if USE_MISTRAL_WRITER:
    MODELS[2:2] = [
        ("Writer fallback (Mistral)", os.getenv("MISTRAL_BASE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")),
        ("Mistral LoRA adapter",      os.getenv("MISTRAL_MODEL", "basmalaalaa029/cv-finetuned-mistral")),
    ]

def main() -> None:
    if not USE_MISTRAL_WRITER:
        print("Skipping Mistral models (USE_MISTRAL_WRITER=false).\n")
    print(f"Downloading {len(MODELS)} models...\n")
    failed = []

    for label, model_id in MODELS:
        print(f"[{label}]  {model_id}")
        try:
            kwargs = {"token": TOKEN} if TOKEN else {}
            phi3_model = os.getenv("PHI3_MODEL", "basmalaalaa029/phi3-cv")
            if model_id == phi3_model and PHI3_ADAPTER_SUBFOLDER:
                kwargs["allow_patterns"] = [f"{PHI3_ADAPTER_SUBFOLDER}/*"]
                print(f"  (subfolder: {PHI3_ADAPTER_SUBFOLDER})")
            snapshot_download(model_id, **kwargs)
            print(f"  ✓ done\n")
        except Exception as exc:
            print(f"  ✗ FAILED: {exc}\n")
            failed.append((label, model_id, str(exc)))

    if failed:
        print("The following models failed to download:")
        for label, model_id, err in failed:
            print(f"  - {label} ({model_id}): {err}")
        sys.exit(1)
    else:
        print("All models downloaded successfully.")

if __name__ == "__main__":
    main()
