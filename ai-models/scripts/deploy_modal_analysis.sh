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

MODAL_BIN="${MODAL_BIN:-}"
if [[ -z "$MODAL_BIN" ]]; then
  if [[ -x "$ROOT/.venv/bin/modal" ]]; then
    MODAL_BIN="$ROOT/.venv/bin/modal"
  else
    MODAL_BIN="$PY -m modal"
  fi
fi

_modal() {
  if [[ "$MODAL_BIN" == *" -m modal" ]]; then
    $PY -m modal "$@"
  else
    "$MODAL_BIN" "$@"
  fi
}

MODAL_PROFILE="${MODAL_PROFILE:-myhywgxtj-arch}"
if [[ -n "$MODAL_PROFILE" ]]; then
  export MODAL_PROFILE
  echo "Using Modal profile: $MODAL_PROFILE"
  if ! _modal profile activate "$MODAL_PROFILE" 2>/dev/null; then
    echo "Profile '$MODAL_PROFILE' not found. Add it with:"
    echo "  $PY -m modal token new --profile $MODAL_PROFILE --activate"
    echo "Log in at modal.com as workspace '$MODAL_PROFILE' before completing the browser flow."
    exit 1
  fi
fi

if ! _modal profile current >/dev/null 2>&1; then
  echo "Run: $PY -m modal setup"
  echo "Or: $PY -m modal token new --profile <workspace> --activate"
  exit 1
fi

echo "Modal profile:"
_modal profile current || true
WORKSPACE="$(_modal token info 2>/dev/null | awk '/Workspace:/ {print $2}')"
if [[ -n "$WORKSPACE" ]]; then
  echo "Modal workspace: $WORKSPACE"
fi

if [[ -n "$MODAL_PROFILE" && -n "$WORKSPACE" && "$MODAL_PROFILE" != "$WORKSPACE" ]]; then
  echo ""
  echo "ERROR: Profile '$MODAL_PROFILE' is linked to workspace '$WORKSPACE'."
  echo "Deploy would target '$WORKSPACE', not '$MODAL_PROFILE'."
  echo ""
  echo "Re-link the profile (log in as $MODAL_PROFILE in the browser when prompted):"
  echo "  $PY -m modal token new --profile $MODAL_PROFILE --activate"
  echo ""
  echo "Or deploy to the linked workspace instead:"
  echo "  MODAL_PROFILE=$WORKSPACE ./scripts/deploy_modal_analysis.sh"
  exit 1
fi

if ! _modal secret list 2>/dev/null | grep -q cv-analysis-secrets; then
  echo ""
  echo "Secret cv-analysis-secrets not found in workspace '$MODAL_PROFILE'."
  echo "Create it with:"
  echo "  1. Set HUGGINGFACE_TOKEN in ai-models/.env"
  echo "  2. ./scripts/create_modal_analysis_secret.sh"
  echo ""
  echo "Or in the Modal UI: https://modal.com/secrets/${MODAL_PROFILE}/main"
  echo "  Name: cv-analysis-secrets"
  echo "  Keys: HF_TOKEN, ANALYSIS_BASE_MODEL_ID, ANALYSIS_ADAPTER_MODEL_ID"
  exit 1
fi

echo "Deploying cv-analysis to Modal..."
if ! _modal deploy analysis/infra/modal/server.py; then
  echo ""
  echo "Deploy failed. Common causes:"
  echo "  - billing spend limit: https://modal.com/settings/billing"
  echo "  - wrong workspace token: $PY -m modal token new --profile $MODAL_PROFILE --activate"
  exit 1
fi

echo ""
echo "Done. Copy the 'analyze' web endpoint URL into .env:"
echo "  MODAL_ENDPOINT_URL=https://myhywgxtj-arch--cv-analysis-cvanalysismodel-analyze.modal.run"
echo "Then restart: .venv/bin/python main.py"
