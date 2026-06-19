#!/usr/bin/env bash
# Optional: print commands to start all three CareerForge services in separate terminals.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cat <<EOF
CareerForge — run each service in its own terminal:

  # MongoDB (once)
  cd $ROOT && docker compose up -d mongo

  # Terminal 1 — Frontend (Node)
  cd $ROOT/frontend && cp -n env.template .env 2>/dev/null; npm install && npm run dev

  # Terminal 2 — Backend (Node)
  cd $ROOT/backend && cp -n env.template .env 2>/dev/null; npm install && npm run dev

  # Terminal 3 — AI models (Python)
  cd $ROOT/ai-models && cp -n env.template .env 2>/dev/null; ./scripts/setup.sh
  ./scripts/run.sh

Use the same JWT_SECRET in backend/.env and ai-models/.env
EOF
