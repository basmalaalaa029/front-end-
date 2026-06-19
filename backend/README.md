# CareerForge Backend

Express API for login, registration, profile, and OAuth (port **5000**).

## Quick start

### 1. MongoDB

From the repo root:

```bash
docker compose up -d mongo
```

Or use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and set `MONGODB_URI` in `.env`.

### 2. Install & run

```bash
cd backend
cp env.template .env
npm install
npm run dev
```

### 3. Frontend

Run the frontend from `frontend/` (`npm run dev`).  
Set `VITE_API_URL=http://localhost:5000/api` in `frontend/.env`.

### 4. JWT secret

Use the **same** `JWT_SECRET` in `backend/.env` and `ai-models/.env` so the AI service accepts login tokens.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Email login |
| GET | `/api/auth/google` | Google OAuth |
| GET | `/api/auth/linkedin` | LinkedIn OAuth |
| GET | `/api/users/profile` | Profile (Bearer token) |
| PUT | `/api/users/profile` | Update profile |

## Google / LinkedIn (optional)

1. Create OAuth apps in [Google Cloud Console](https://console.cloud.google.com/) and [LinkedIn Developers](https://www.linkedin.com/developers/).
2. Add redirect URIs:
   - `http://localhost:5000/api/auth/google/callback`
   - `http://localhost:5000/api/auth/linkedin/callback`
3. Put client IDs/secrets in `backend/.env`.

Email register/login works without OAuth credentials.
