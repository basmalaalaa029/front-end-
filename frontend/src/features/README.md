# Feature modules (vertical slices)

Architecture diagram: [`cv_builder_architecture.svg`](../../cv_builder_architecture.svg)  
Full reference: [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)

Each folder is a **vertical slice**: UI, API client, types, hooks, and stores for one user-facing capability. Import from the slice root (`@/features/<name>`), not from deep paths in other slices.

## Slices

| Feature | Route(s) | Backend slice |
|---------|----------|---------------|
| `landing` | `/` | — |
| `auth` | `/login`, `/register`, `/auth/callback` | `backend/` :5000 |
| `hub-shell` | (layout wrapper) | — |
| `dashboard` | `/dashboard` | — |
| `cv-analysis` | `/dashboard/analyzer` | `analysis/` → `POST /analyze` :8000 |
| `cv-editor` | `/dashboard/editor`, `/dashboard/editor/build/:id` | `cv/` → `POST /generate` :8000 |
| `job-agent` | `/dashboard/jobs` | `job_match/` → `POST /jobs/match` :8000 |
| `interview` | `/dashboard/interview` | `interview/` → `POST /interview/start` :8000 |
| `profile` | `/profile` | `backend/` `/users` :5000 |
| `i18n` | (provider) | — |

## Slice layout

```
features/<slice>/
  components/   # pages and UI parts
  lib/          # API clients and helpers
  hooks/        # React Query hooks (server state)
  types/        # TypeScript types
  stores/       # zustand (client/draft state)
  data/         # static data (optional)
  index.ts      # public exports only
```

## Rules

1. **No cross-slice deep imports** — use `@/features/<slice>` barrel `index.ts`.
2. **Shared hub chrome** lives in `hub-shell` only.
3. **Auth session** — `auth` owns `useAuthStore`; CV Agent calls use `src/shared/lib/cv-agent-client.ts`.
4. **Server state** — React Query hooks in each slice; Zustand for local drafts only.
5. **New capability** — add frontend slice + backend package + wire route in `App.tsx`.
