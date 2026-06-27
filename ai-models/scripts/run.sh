#!/usr/bin/env bash
# Start AI models API (always uses .venv python — no activate needed)
set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python3"

if [[ ! -x "$PY" ]]; then
  echo "No .venv found. Run first: ./scripts/setup.sh"
  exit 1
fi

if ! "$PY" -c "import dotenv" 2>/dev/null; then
  cat <<EOF
❌ Dependencies not installed in .venv (missing python-dotenv).

Run setup first:
  ./scripts/setup.sh

On Ubuntu, if venv creation fails:
  sudo apt install python3-venv python3.12-venv
  ./scripts/setup.sh

EOF
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Create .env from the template and edit secrets:"
  echo "  cp env.template .env"
  exit 1
fi

# Bundled ffmpeg (./scripts/install_ffmpeg.sh) — no sudo required
FFMPEG_DIR="$(pwd)/vendor/ffmpeg-static"
if [[ -x "$FFMPEG_DIR/ffmpeg" ]]; then
  export PATH="$FFMPEG_DIR:$PATH"
fi

exec "$PY" main.py
