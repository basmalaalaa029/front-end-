#!/usr/bin/env bash
# Create cv-analysis-secrets in Modal (workspace must match MODAL_PROFILE).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PY:-$ROOT/.venv/bin/python3}"
MODAL_PROFILE="${MODAL_PROFILE:-myhywgxtj-arch}"
export MODAL_PROFILE

# Load HUGGINGFACE_TOKEN from .env if present
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^(HUGGINGFACE_TOKEN|HF_TOKEN|ANALYSIS_BASE_MODEL_ID|ANALYSIS_ADAPTER_MODEL_ID|ANALYSIS_MERGED_MODEL_ID)=' "$ROOT/.env" 2>/dev/null || true)
  set +a
fi

HF_TOKEN="${HF_TOKEN:-${HUGGINGFACE_TOKEN:-}}"
BASE_ID="${ANALYSIS_BASE_MODEL_ID:-OsamaHayba/qwen-ats-merged-stage1}"
ADAPTER_ID="${ANALYSIS_ADAPTER_MODEL_ID:-OsamaHayba/cv-analysis-final-stage2}"
MERGED_ID="${ANALYSIS_MERGED_MODEL_ID:-}"

if [[ -z "$HF_TOKEN" ]]; then
  echo "HUGGINGFACE_TOKEN is empty in ai-models/.env"
  echo ""
  echo "1. Get a token: https://huggingface.co/settings/tokens (Read access)"
  echo "2. Add to ai-models/.env:"
  echo "     HUGGINGFACE_TOKEN=hf_xxxxxxxx"
  echo "3. Re-run: ./scripts/create_modal_analysis_secret.sh"
  echo ""
  echo "Or create the secret in the Modal UI:"
  echo "  https://modal.com/secrets/${MODAL_PROFILE}/main"
  echo "  Name: cv-analysis-secrets"
  echo "  Keys: HF_TOKEN, ANALYSIS_BASE_MODEL_ID, ANALYSIS_ADAPTER_MODEL_ID"
  exit 1
fi

"$PY" -m modal profile activate "$MODAL_PROFILE" >/dev/null

WORKSPACE="$("$PY" -m modal token info 2>/dev/null | awk '/Workspace:/ {print $2}')"
if [[ -n "$WORKSPACE" && "$WORKSPACE" != "$MODAL_PROFILE" ]]; then
  echo "ERROR: profile '$MODAL_PROFILE' is linked to workspace '$WORKSPACE'"
  exit 1
fi

if "$PY" -m modal secret list 2>/dev/null | grep -q cv-analysis-secrets; then
  echo "Secret cv-analysis-secrets already exists in $MODAL_PROFILE."
  echo "To replace it: $PY -m modal secret delete cv-analysis-secrets"
  exit 0
fi

echo "Creating cv-analysis-secrets in workspace: $MODAL_PROFILE"

if [[ -n "$MERGED_ID" ]]; then
  "$PY" -m modal secret create cv-analysis-secrets \
    HF_TOKEN="$HF_TOKEN" \
    ANALYSIS_MERGED_MODEL_ID="$MERGED_ID"
else
  "$PY" -m modal secret create cv-analysis-secrets \
    HF_TOKEN="$HF_TOKEN" \
    ANALYSIS_BASE_MODEL_ID="$BASE_ID" \
    ANALYSIS_ADAPTER_MODEL_ID="$ADAPTER_ID"
fi

echo "Done. Run: ./scripts/deploy_modal_analysis.sh"
