# CareerForge Frontend

React + Vite app with vertical feature slices under `src/features/`.

## Quick start

```bash
cd frontend
cp env.template .env
npm install
npm run dev
```

Open http://localhost:5173

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `http://localhost:5000/api` | Auth / profile API |
| `VITE_CV_AGENT_URL` | `http://localhost:8000` | AI services (analysis, CV gen, jobs, interview) |

## Feature slices

See [`src/features/README.md`](src/features/README.md) for the slice map and import rules.
