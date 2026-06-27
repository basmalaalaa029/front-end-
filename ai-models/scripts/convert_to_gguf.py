"""
scripts/convert_to_gguf.py
==========================
ONE-TIME conversion of the fine-tuned LoRA models to quantized GGUF, so they can
run fast on CPU via llama.cpp. Run this on a machine with a GPU (e.g. Colab) —
the merge step is much faster there. Then download the produced ``.gguf`` files
into ``ai-models/models/gguf/`` on the CPU box.

What it does for each model:
  1. Load base model + LoRA adapter and merge them (`merge_and_unload`).
  2. Convert the merged HF model to GGUF f16 (llama.cpp `convert_hf_to_gguf.py`).
  3. Quantize f16 -> Q4_K_M (llama.cpp `llama-quantize`).

Off-the-shelf models (Qwen2.5-7B-Instruct, Phi-3-mini base) do NOT need this —
download their community GGUF directly from Hugging Face.

Prerequisites:
    pip install transformers peft torch accelerate huggingface-hub
    # llama.cpp (for convert + quantize); the script can clone+build it for you.

Usage:
    # convert phi3 CV writer fine-tune:
    python scripts/convert_to_gguf.py --models phi3

    # custom quant / output dir / existing llama.cpp checkout:
    python scripts/convert_to_gguf.py --models phi3 --quant Q4_K_M \
        --llama-cpp-dir /path/to/llama.cpp --out-dir models/gguf
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

try:
    from load_env import load_env

    load_env()
except Exception:
    pass

TOKEN = os.getenv("HUGGINGFACE_TOKEN", "") or None

# label -> (base_model, lora_adapter, adapter_subfolder, output_filename_stem)
FINE_TUNES = {
    "phi3": (
        os.getenv("PHI3_BASE_MODEL", "microsoft/Phi-3-mini-4k-instruct"),
        os.getenv("PHI3_MODEL", "basmalaalaa029/phi3-cv"),
        os.getenv("PHI3_ADAPTER_SUBFOLDER", "checkpoint-200"),
        "phi3-cv",
    ),
}


def _run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def ensure_llama_cpp(explicit: str | None) -> Path:
    """Return a llama.cpp checkout with convert script + built llama-quantize."""
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            sys.exit(f"--llama-cpp-dir '{path}' does not exist.")
        return path

    path = _ROOT / ".llama.cpp"
    if not path.exists():
        print(f"Cloning llama.cpp into {path} …")
        _run(["git", "clone", "--depth", "1", "https://github.com/ggerganov/llama.cpp", str(path)])
    # Install the Python deps used by convert_hf_to_gguf.py (gguf, sentencepiece, …).
    reqs = path / "requirements.txt"
    if reqs.exists():
        print("Installing llama.cpp Python requirements (for the convert script) …")
        try:
            _run([sys.executable, "-m", "pip", "install", "-q", "-r", str(reqs)])
        except subprocess.CalledProcessError as exc:
            print(f"  (warning) could not install llama.cpp requirements: {exc}")
    # Build llama-quantize if missing.
    quant = _find_quantize(path)
    if quant is None:
        print("Building llama.cpp (llama-quantize) …")
        _run(["cmake", "-B", str(path / "build"), "-S", str(path)])
        _run(["cmake", "--build", str(path / "build"), "--config", "Release", "-j",
              "--target", "llama-quantize"])
    return path


def _find_quantize(llama_dir: Path) -> Path | None:
    for cand in [
        llama_dir / "build" / "bin" / "llama-quantize",
        llama_dir / "build" / "llama-quantize",
        llama_dir / "llama-quantize",
    ]:
        if cand.exists():
            return cand
    return None


def merge_lora(base: str, adapter: str, subfolder: str, dest: Path) -> None:
    """Merge a LoRA adapter into its base model and save the merged HF model."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"  Loading base: {base}")
    model = AutoModelForCausalLM.from_pretrained(
        base, torch_dtype=torch.float16, trust_remote_code=True, token=TOKEN,
    )
    adapter_kw = {"token": TOKEN}
    if subfolder:
        adapter_kw["subfolder"] = subfolder
    print(f"  Applying LoRA: {adapter}" + (f" (subfolder={subfolder})" if subfolder else ""))
    model = PeftModel.from_pretrained(model, adapter, **adapter_kw)
    print("  Merging adapter into base weights …")
    model = model.merge_and_unload()
    model.save_pretrained(dest, safe_serialization=True)

    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True, token=TOKEN)
    tok.save_pretrained(dest)
    print(f"  Merged model saved to {dest}")


def convert_and_quantize(merged_dir: Path, out_stem: str, out_dir: Path,
                         quant: str, llama_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f16_path = out_dir / f"{out_stem}-f16.gguf"
    final_path = out_dir / f"{out_stem}-{quant}.gguf"

    convert_script = llama_dir / "convert_hf_to_gguf.py"
    if not convert_script.exists():
        sys.exit(f"convert_hf_to_gguf.py not found in {llama_dir}")
    print("  Converting merged model -> GGUF f16 …")
    _run([sys.executable, str(convert_script), str(merged_dir),
          "--outfile", str(f16_path), "--outtype", "f16"])

    quant_bin = _find_quantize(llama_dir)
    if quant_bin is None:
        sys.exit("llama-quantize binary not found; build llama.cpp first.")
    print(f"  Quantizing f16 -> {quant} …")
    _run([str(quant_bin), str(f16_path), str(final_path), quant])

    if f16_path.exists():
        f16_path.unlink()  # drop the large intermediate
    print(f"  ✓ {final_path} ({final_path.stat().st_size / 1e9:.1f} GB)")
    return final_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge LoRA + convert to quantized GGUF.")
    ap.add_argument("--models", nargs="+", choices=sorted(FINE_TUNES), default=["phi3", "ats"],
                    help="Which fine-tunes to convert.")
    ap.add_argument("--quant", default="Q4_K_M", help="Quantization type (default Q4_K_M).")
    ap.add_argument("--out-dir", default=str(_ROOT / "models" / "gguf"),
                    help="Where to write the .gguf files.")
    ap.add_argument("--llama-cpp-dir", default=None,
                    help="Existing llama.cpp checkout (otherwise cloned+built automatically).")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    llama_dir = ensure_llama_cpp(args.llama_cpp_dir)

    failed = []
    for key in args.models:
        base, adapter, subfolder, stem = FINE_TUNES[key]
        print(f"\n=== {key}: {base} + {adapter} ===")
        try:
            with tempfile.TemporaryDirectory(prefix=f"merge-{stem}-") as tmp:
                merged = Path(tmp) / "merged"
                merge_lora(base, adapter, subfolder, merged)
                convert_and_quantize(merged, stem, out_dir, args.quant, llama_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ FAILED: {exc}")
            failed.append((key, str(exc)))

    if failed:
        print("\nSome conversions failed:")
        for key, err in failed:
            print(f"  - {key}: {err}")
        sys.exit(1)
    print(f"\nDone. Copy the .gguf files from {out_dir} to ai-models/models/gguf/ on the CPU box.")


if __name__ == "__main__":
    main()
