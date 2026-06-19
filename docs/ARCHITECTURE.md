# CareerPilot — Vertical Slice Architecture

Reference diagram: [`cv_builder_architecture.svg`](../cv_builder_architecture.svg)

## Layers

| Layer | Location | Port |
|-------|----------|------|
| Frontend (React) | `frontend/src/features/*` | 5173 |
| Backend (Express) | `backend/src/` | 5000 |
| AI Services (FastAPI) | `ai-models/cv_agent/` | 8000 |

## Frontend slices

Each folder under `frontend/src/features/` is a vertical slice: components, lib, types, hooks, stores.

| Slice | Route | Backend |
|-------|-------|---------|
| `auth` | `/login`, `/register` | `backend/` |
| `cv-editor` | `/dashboard/editor/*` | `cv/` → `/generate` |
| `cv-analysis` | `/dashboard/analyzer` | `analysis/` → `/analyze` — see [ANALYSIS.md](./ANALYSIS.md) |
| `job-agent` | `/dashboard/jobs` | `job_match/` → `/jobs/match` |
| `interview` | `/dashboard/interview` | `interview/` → `/interview/*` |
| `hub-shell` | layout wrapper | — |

### Shared frontend

- `frontend/src/shared/lib/cv-agent-client.ts` — JWT-authenticated fetch to AI services
- `frontend/src/shared/lib/query-client.ts` — React Query defaults
- `frontend/src/lib/api.ts` — Axios client for auth API

## AI Services slices (`ai-models/cv_agent/`)

| Package | Endpoints | Purpose |
|---------|-----------|---------|
| `analysis/` | `POST /analyze`, `/analyze/upload` | ATS scoring |
| `cv/` | `POST /generate`, `GET /status`, `/result`, `/pdf` | CV generation |
| `job_match/` | `POST /jobs/match`, `GET /jobs/results/{id}` | Job matching |
| `interview/` | `POST /interview/start`, `/answer`, `/evaluate` | Interview sim |

### Shared AI infra (`cv_agent/app/`)

| Module | Purpose |
|--------|---------|
| `config.py` | Env flags, `PipelineConfig`, logging |
| `queue.py` | GPU worker queue |
| `auth.py` | JWT verification middleware |
| `api.py` | FastAPI app factory + route registration |

## Authentication flow

Node.js `backend/` (port 5000) is the **only** authentication service.

1. User registers or logs in via `backend/` (`POST /api/auth/register`, `/login`, or OAuth) → receives JWT
2. Frontend stores token in `useAuthStore` and validates session via `GET /api/auth/me`
3. All CV Agent requests include `Authorization: Bearer <token>`
4. `cv_agent/app/auth.py` verifies the JWT (same `JWT_SECRET` as backend) — no login on Python
5. For isolated API testing only: `CV_AGENT_AUTH_DISABLED=true` in `ai-models/.env`

## Environment

Each service has its own `.env` file:

| File | Purpose |
|------|---------|
| `frontend/env.template` | Vite (`VITE_*` only) |
| `backend/env.template` | MongoDB, OAuth, JWT |
| `ai-models/env.template` | Models, analysis, JWT |

Copy each to `.env` in the same folder. **`JWT_SECRET` must match** in `backend/.env` and `ai-models/.env`.

## Local development

```bash
# Terminal 1 — frontend
cd frontend && npm run dev

# Terminal 2 — backend (MongoDB via docker compose up -d mongo)
cd backend && npm run dev

# Terminal 3 — AI models
cd ai-models && source .venv/bin/activate && python3 main.py
```
