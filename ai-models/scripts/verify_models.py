"""
scripts/verify_models.py — verify analysis model runtime and Gemini CV config.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from load_env import load_env

load_env()


def check(label: str, fn):
    print(f"\n[{label}] loading...")
    try:
        result = fn()
        preview = str(result)[:100].replace("\n", " ")
        print(f"  ✓ response: {preview}")
        return True
    except Exception as exc:
        print(f"  ✗ FAILED: {exc}")
        return False


def main() -> None:
    from cv_agent.app.config import PipelineConfig
    from cv_analysis.judges.model_runtime import get_analysis_runtime, judge_chat

    cfg = PipelineConfig()
    an_rt = get_analysis_runtime()
    results = []

    if (cfg.gemini_api_key or "").strip():
        print(f"\n[CV Writer (Gemini)] configured model={cfg.gemini_model}")
        results.append(True)
    else:
        print("\n[CV Writer (Gemini)] ✗ GEMINI_API_KEY not set")
        results.append(False)

    results.append(check(
        "HR Judge (Qwen2.5)",
        lambda: judge_chat(
            an_rt.hr_judge_pipe(cfg), "You are an HR evaluator.",
            "Rate this CV in one word.",
        ),
    ))

    results.append(check(
        "ATS Judge (Qwen + LoRA)",
        lambda: judge_chat(
            an_rt.ats_judge_pipe(cfg), "You are an ATS system.",
            'Return valid JSON only: {"overall_score": 85}',
        ),
    ))

    print()
    if all(results):
        print("All models working correctly.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
