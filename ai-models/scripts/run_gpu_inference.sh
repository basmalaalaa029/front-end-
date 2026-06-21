#!/usr/bin/env bash
# Start the fine-tuned Qwen judge on a GPU machine (OpenAI-compatible API).
#
# Usage (on GPU box, from ai-models/):
#   export HUGGINGFACE_TOKEN=hf_...
#   export GPU_INFERENCE_API_KEY=choose-a-secret   # optional
#   ./scripts/run_gpu_inference.sh
#
# CPU app .env:
#   CV_ANALYSIS_INFERENCE_MODE=remote
#   CV_ANALYSIS_LLAMA_SERVER_URL=http://YOUR_GPU_IP:8080
#   CV_ANALYSIS_REMOTE_API_KEY=choose-a-secret     # must match GPU_INFERENCE_API_KEY

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${GPU_INFERENCE_PORT:-8080}"
HOST="${GPU_INFERENCE_HOST:-0.0.0.0}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

PYTHON="${ROOT}/.venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

echo "Starting GPU inference service on ${HOST}:${PORT}"
echo "  base   : ${JUDGE_BASE_MODEL:-OsamaHayba/qwen-ats-merged-stage1}"
echo "  adapter: ${JUDGE_ADAPTER_PATH:-OsamaHayba/cv-analysis-final-stage2}"
echo "  health : http://127.0.0.1:${PORT}/health"
echo ""

exec "$PYTHON" -m uvicorn gpu_inference.service:app \
  --host "$HOST" \
  --port "$PORT" \
  --log-level "${LOG_LEVEL:-info}"
