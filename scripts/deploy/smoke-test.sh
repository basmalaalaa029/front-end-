#!/usr/bin/env bash
# Post-deploy smoke test for CareerPilot services.
# Usage:
#   ./scripts/deploy/smoke-test.sh \
#     --frontend https://your-app.vercel.app \
#     --backend https://your-backend.onrender.com \
#     --ai https://your-ai.onrender.com
set -euo pipefail

FRONTEND=""
BACKEND=""
AI=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --frontend) FRONTEND="$2"; shift 2 ;;
    --backend)  BACKEND="$2"; shift 2 ;;
    --ai)       AI="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$FRONTEND" || -z "$BACKEND" || -z "$AI" ]]; then
  echo "Usage: $0 --frontend URL --backend URL --ai URL"
  exit 1
fi

pass=0
fail=0

check() {
  local name="$1" url="$2" expect="$3"
  printf "Checking %-20s %s ... " "$name" "$url"
  if resp=$(curl -sf --max-time 120 "$url" 2>/dev/null); then
    if echo "$resp" | grep -q "$expect"; then
      echo "PASS"
      pass=$((pass + 1))
    else
      echo "FAIL (unexpected response)"
      echo "  Got: ${resp:0:200}"
      fail=$((fail + 1))
    fi
  else
    echo "FAIL (HTTP error or timeout — Render free tier may be cold-starting)"
    fail=$((fail + 1))
  fi
}

check "frontend" "$FRONTEND" "<!DOCTYPE html>"
check "backend health" "$BACKEND/api/health" '"ok":true'
check "AI health" "$AI/health" '"status":"ok"'

echo ""
echo "Results: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
