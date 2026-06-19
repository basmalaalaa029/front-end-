"""
scripts/download_gguf.py
========================
Download the fine-tuned CV analysis GGUF model into ``ai-models/models/gguf/``.

Model:
  - cv-analysis-Q4_K_M.gguf  — basmalaalaa029/cv-analysis-final-GGUF

Usage:
    python3 scripts/download_gguf.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

try:
    from load_env import load_env

    load_env()
except Exception:
    pass

from huggingface_hub import hf_hub_download

TOKEN = os.getenv("HUGGINGFACE_TOKEN", "") or None
OUT_DIR = Path(os.getenv("GGUF_DIR", str(_ROOT / "models" / "gguf")))
if not OUT_DIR.is_absolute():
    OUT_DIR = _ROOT / OUT_DIR

# (label, repo_id, filename_in_repo, local_filename)
# local_filename must match ATS_GGUF_PATH in app/config.py.
DOWNLOADS = [
    (
        "CV Analysis / ATS judge (fine-tuned Qwen GGUF — Q4_K_M)",
        os.getenv("ATS_GGUF_REPO", "basmalaalaa029/cv-analysis-gguf"),
        os.getenv("ATS_GGUF_FILE", "cv-analysis-Q4_K_M.gguf"),
        os.getenv("ATS_GGUF_PATH", "cv-analysis-Q4_K_M.gguf"),
    ),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {len(DOWNLOADS)} GGUF model(s) into {OUT_DIR}\n")
    failed = []

    for label, repo_id, filename, local_name in DOWNLOADS:
        dest = OUT_DIR / Path(local_name).name
        if dest.exists():
            print(f"[{label}] already present: {dest.name}\n")
            continue
        print(f"[{label}]  {repo_id}/{filename}")
        try:
            cached = hf_hub_download(repo_id=repo_id, filename=filename, token=TOKEN)
            # Place under the expected local filename without copying the blob twice.
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            os.symlink(os.path.realpath(cached), dest)
            print(f"  ✓ {dest.name}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ FAILED: {exc}\n")
            failed.append((label, str(exc)))

    if failed:
        print("Some downloads failed:")
        for label, err in failed:
            print(f"  - {label}: {err}")
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
