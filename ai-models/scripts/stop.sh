#!/usr/bin/env bash
# Stop CV Agent processes started from this repo (ports 8000–8002).
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"

echo "Stopping CV Agent in ${REPO}…"

# Reloader + worker children
pkill -f "${REPO}/.venv/bin/python3 main.py" 2>/dev/null || true
pkill -f "${REPO}/main.py" 2>/dev/null || true

if command -v fuser >/dev/null 2>&1; then
  for port in 8000 8001 8002 8080; do
    fuser -k "${port}/tcp" 2>/dev/null || true
  done
fi

sleep 1

if command -v ss >/dev/null 2>&1; then
  if ss -tlnp 2>/dev/null | grep -qE ':800[0-2] '; then
    echo "⚠️  Something is still listening on 8000–8002:"
    ss -tlnp 2>/dev/null | grep -E ':800[0-2] ' || true
    exit 1
  fi
fi

echo "✅ Ports 8000–8002 are free."
