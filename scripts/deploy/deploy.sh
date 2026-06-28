#!/usr/bin/env bash
# Interactive deployment helper — prints platform-specific next steps.
# Full guide: docs/DEPLOYMENT.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "CareerPilot deployment checklist"
echo "================================="
echo ""

step=1

echo "$step. MongoDB Atlas (free M0)"
echo "   → https://www.mongodb.com/cloud/atlas"
echo "   → Create cluster, user, allow 0.0.0.0/0"
echo "   → Copy connection string to MONGODB_URI"
echo "   → Template: backend/env.production.template"
((step++))
echo ""

echo "$step. Modal CV analysis (GPU)"
echo "   cd ai-models"
echo "   ./scripts/setup.sh"
echo "   ./scripts/create_modal_analysis_secret.sh"
echo "   ./scripts/deploy_modal_analysis.sh"
echo "   → Copy MODAL_ENDPOINT_URL to Render AI env"
((step++))
echo ""

echo "$step. Render (backend + AI)"
echo "   → https://dashboard.render.com → New → Blueprint"
echo "   → Connect repo; uses render.yaml at repo root"
echo "   → Set MONGODB_URI, FRONTEND_URL, API keys when prompted"
echo "   → JWT_SECRET auto-syncs from backend to AI service"
((step++))
echo ""

echo "$step. Vercel (frontend)"
echo "   → https://vercel.com/new → Import repo"
echo "   → Root directory: frontend"
echo "   → Set VITE_API_URL and VITE_CV_AGENT_URL from Render URLs"
echo "   → Template: frontend/env.production.template"
((step++))
echo ""

echo "$step. Smoke test"
echo "   ./scripts/deploy/smoke-test.sh \\"
echo "     --frontend https://YOUR-APP.vercel.app \\"
echo "     --backend https://careerpilot-backend.onrender.com \\"
echo "     --ai https://careerpilot-ai.onrender.com"
echo ""

if [[ -f frontend/dist/index.html ]]; then
  echo "✓ Frontend build exists (frontend/dist/)"
else
  echo "○ Run: cd frontend && npm run build"
fi

if [[ -f render.yaml && -f frontend/vercel.json && -f ai-models/requirements-prod.txt ]]; then
  echo "✓ Deployment config files present"
else
  echo "✗ Missing deployment config — see docs/DEPLOYMENT.md"
fi

echo ""
echo "See docs/DEPLOYMENT.md for full instructions."
