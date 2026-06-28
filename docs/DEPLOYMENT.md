# CareerPilot — Production Deployment Guide

Full-stack deployment on free/low-cost platforms: **MongoDB Atlas**, **Vercel** (frontend), **Render** (backend + AI API), and **Modal** (GPU CV analysis).

## Architecture

```
Browser → Vercel (frontend)
            ├→ Render backend (:5000) → MongoDB Atlas
            └→ Render AI API (:8000) → Modal / Gemini / Groq
```

## Prerequisites

- GitHub repo connected to [Vercel](https://vercel.com) and [Render](https://render.com)
- Accounts: MongoDB Atlas, Modal
- API keys: `GEMINI_API_KEY`, `GROQ_API_KEY`, `HUGGINGFACE_TOKEN`
- Optional: Google/LinkedIn OAuth credentials

## 1. MongoDB Atlas (database)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) → **Create** → **M0 FREE** cluster.
2. **Database Access** → Add user (username + password).
3. **Network Access** → Add IP `0.0.0.0/0` (or restrict to Render IPs later).
4. **Connect** → Drivers → copy connection string:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/careerpilot?retryWrites=true&w=majority
   ```
5. Save as `MONGODB_URI` for the backend Render service.

Verify locally (optional):

```bash
./scripts/deploy/verify-atlas-uri.sh "$MONGODB_URI"
```

## 2. Modal (CV analysis GPU)

From `ai-models/`:

```bash
cp env.template .env
# Set HUGGINGFACE_TOKEN and MODAL_PROFILE in .env
./scripts/setup.sh
./scripts/create_modal_analysis_secret.sh   # first time only
./scripts/deploy_modal_analysis.sh
```

Copy the printed URL into `MODAL_ENDPOINT_URL` for the AI Render service.

Full guide: [ai-models/analysis/infra/modal/README.md](../ai-models/analysis/infra/modal/README.md)

## 3. Backend + AI on Render

**Option A — Full-stack Blueprint (recommended)**

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect this repo; Render reads [render.yaml](../render.yaml) (deploys both backend and AI)
3. Set sync-false env vars when prompted:

| Variable | Service | Example |
|----------|---------|---------|
| `MONGODB_URI` | backend | Atlas connection string |
| `FRONTEND_URL` | both | `https://your-app.vercel.app` |
| `ALLOWED_ORIGINS` | AI | `https://your-app.vercel.app` |
| `MODAL_ENDPOINT_URL` | AI | From Modal deploy |
| `GEMINI_API_KEY` | AI | Gemini API key |
| `GROQ_API_KEY` | AI | Groq API key |
| `HUGGINGFACE_TOKEN` | AI | HF token |

`JWT_SECRET` auto-syncs from backend to the AI service via the root blueprint.

**Option B — Individual blueprints**

- Backend only: [backend/render.yaml](../backend/render.yaml)
- AI only: [ai-models/render.yaml](../ai-models/render.yaml)

**Option C — Manual Web Service (backend)**

- Root directory: `backend`
- Build: `npm install`
- Start: `npm start`
- Health check: `/api/health`

Update OAuth redirect URIs in Google/LinkedIn consoles to match production callback URLs.

## 4. AI models on Render (manual only)

If not using the root blueprint:

- Root directory: `ai-models`
- Build: `pip install -r requirements-prod.txt`
- Start: `gunicorn -w 1 -k uvicorn.workers.UvicornWorker cv_agent.app.api:app --bind 0.0.0.0:$PORT --timeout 300`
- Health check: `/health`

After deploy, `GET /health` should show `analysis_ready: true` and `cv_writer_ready: true`.

## 5. Frontend on Vercel

1. [Vercel Dashboard](https://vercel.com/new) → Import repo
2. Root directory: `frontend`
3. Framework: Vite (auto-detected)
4. Build env vars:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com/api` |
| `VITE_CV_AGENT_URL` | `https://your-ai.onrender.com` |
| `VITE_OAUTH_CALLBACK_URL` | `https://your-app.vercel.app/auth/callback` |
| `VITE_OAUTH_GOOGLE_URL` | `https://your-backend.onrender.com/api/auth/google` |
| `VITE_OAUTH_LINKEDIN_URL` | `https://your-backend.onrender.com/api/auth/linkedin` |

SPA routing is handled by [frontend/vercel.json](../frontend/vercel.json).

## 6. Post-deploy checklist

```bash
./scripts/deploy/smoke-test.sh \
  --frontend https://your-app.vercel.app \
  --backend https://your-backend.onrender.com \
  --ai https://your-ai.onrender.com
```

Manual checks:

1. Register/login on the frontend
2. `GET /api/health` on backend → `{ "ok": true }`
3. `GET /health` on AI → `analysis_ready` and `cv_writer_ready` are `true`
4. Test CV analysis, CV generation, job match, interview
5. OAuth login (if configured)

## Free-tier notes

- Render free services spin down after ~15 min idle (30–60s cold start).
- AI service uses API-only mode (`requirements-prod.txt`) — no local GPU models.
- Interview voice (Whisper/Piper) is disabled in production; text interview works via Groq.
- Upgrade path: Render Starter ($7/mo) if AI service OOMs on 512 MB.

## Files reference

| File | Purpose |
|------|---------|
| [frontend/vercel.json](../frontend/vercel.json) | SPA fallback rewrites |
| [backend/render.yaml](../backend/render.yaml) | Render blueprint — backend |
| [ai-models/render.yaml](../ai-models/render.yaml) | Render blueprint — AI API |
| [ai-models/requirements-prod.txt](../ai-models/requirements-prod.txt) | Slim production deps |
| [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) | CI: lint + build |
