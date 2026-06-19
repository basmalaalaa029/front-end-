# CareerForge

AI-powered CV builder: analyze resumes, generate tailored CVs, match jobs, and practice interviews.

## Quick start

From the **repo root**, `npm run dev` starts the frontend. For the full stack, use three terminals:

```bash
npm run install:all    # once — installs frontend + backend deps
npm run dev            # frontend on http://localhost:5173
npm run dev:backend    # auth API on http://localhost:5000 (needs MongoDB)
# ai-models: cd ai-models && source .venv/bin/activate && python3 main.py
```

Or run each service from its folder with native tooling:

### 1. Frontend (Node — port 5173)

```bash
cd frontend
cp env.template .env
npm install
npm run dev
```

### 2. Backend (Node + MongoDB — port 5000)

```bash
# From repo root — start MongoDB once
docker compose up -d mongo

cd backend
cp env.template .env
npm install
npm run dev
```

### 3. AI models (Python — port 8000)

**Prerequisite (Ubuntu/Debian once):** `sudo apt install python3-venv python3.12-venv`

```bash
cd ai-models
cp env.template .env    # set HUGGINGFACE_TOKEN; match JWT_SECRET with backend
./scripts/setup.sh      # once: creates .venv, installs requirements
./scripts/run.sh        # start server (no activate needed)
```

If port 8000 is busy: `cd ai-models && ./scripts/stop.sh && ./scripts/run.sh`

**Important:** use the same `JWT_SECRET` in `backend/.env` and `ai-models/.env`.

## Project layout

```
careerforge/
├── frontend/     React + Vite (vertical feature slices)
├── backend/      Express auth API (login, OAuth, profile)
├── ai-models/    FastAPI AI services (analysis, CV gen, jobs, interview)
└── docs/         Architecture reference
```

## Optional shortcuts (from repo root)

```bash
npm run dev:frontend
npm run dev:backend
```

AI models always run with Python directly (`cd ai-models && python3 main.py` or `.venv/bin/python3 main.py`).

## Documentation

- [Architecture overview](docs/ARCHITECTURE.md)
- [CV analysis pipeline](docs/ANALYSIS.md)
- [Backend README](backend/README.md)
- [AI models README](ai-models/README.md)
