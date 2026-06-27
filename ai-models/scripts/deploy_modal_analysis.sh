#!/usr/bin/env bash
# Deploy CV analysis to Modal (GPU). Run from ai-models/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PY:-$ROOT/.venv/bin/python3}"
PIP="${PIP:-$ROOT/.venv/bin/pip3}"

if [[ ! -x "$PY" ]]; then
  echo "No virtualenv found. Run first:"
  echo "  ./scripts/setup.sh"
  exit 1
fi

if ! command -v modal >/dev/null 2>&1 && [[ ! -x "$ROOT/.venv/bin/modal" ]]; then
  echo "Installing modal CLI..."
  "$PIP" install -r requirements-modal.txt
fi

MODAL_BIN="${MODAL_BIN:-$ROOT/.venv/bin/modal}"
MODAL_PROFILE="${MODAL_PROFILE:-}"
if [[ -n "$MODAL_PROFILE" ]]; then
  export MODAL_PROFILE
  echo "Using Modal profile: $MODAL_PROFILE"
  if ! "$MODAL_BIN" profile activate "$MODAL_PROFILE" 2>/dev/null; then
    echo "Profile '$MODAL_PROFILE' not found. Add it with:"
    echo "  $MODAL_BIN token new --profile $MODAL_PROFILE --activate"
    echo "Log in at modal.com as that workspace before completing the browser flow."
    exit 1
  fi
fi

if ! "$MODAL_BIN" profile current >/dev/null 2>&1; then
  echo "Run: $MODAL_BIN setup"
  echo "Or: $MODAL_BIN token new --profile <workspace> --activate"
  exit 1
fi

echo "Modal profile:"
"$MODAL_BIN" profile current || true
WORKSPACE="$("$MODAL_BIN" token info 2>/dev/null | awk '/Workspace:/ {print $2}')"
if [[ -n "$WORKSPACE" ]]; then
  echo "Modal workspace: $WORKSPACE"
fi

if ! "$MODAL_BIN" secret list 2>/dev/null | grep -q cv-analysis-secrets; then
  echo ""
  echo "Create secret cv-analysis-secrets first, e.g.:"
  echo "  $MODAL_BIN secret create cv-analysis-secrets \\"
  echo "    HF_TOKEN=\$HUGGINGFACE_TOKEN \\"
  echo "    ANALYSIS_BASE_MODEL_ID=OsamaHayba/qwen-ats-merged-stage1 \\"
  echo "    ANALYSIS_ADAPTER_MODEL_ID=bosyalaa224/cv-analysis-final-stage2"
  echo ""
  echo "Use your Hugging Face model repo if you uploaded a fine-tune under your account."
  exit 1
fi

echo "Deploying cv-analysis to Modal..."
"$MODAL_BIN" deploy analysis/infra/modal/server.py

echo ""
echo "Done. Copy the 'analyze' web endpoint URL into .env:"
echo "  MODAL_ENDPOINT_URL=https://<workspace>--cv-analysis-....modal.run"
echo "Then restart: .venv/bin/python main.py"
