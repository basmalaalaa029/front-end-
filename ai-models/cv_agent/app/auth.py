"""JWT verification middleware — same secret as backend."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI, Request


_PUBLIC_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


def _allowed_origins() -> set[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080",
    )
    return {o.strip() for o in raw.split(",") if o.strip()}


def _cors_headers(request: "Request") -> dict[str, str]:
    """JWT short-circuit responses bypass CORSMiddleware — add ACAO manually."""
    origin = request.headers.get("origin", "")
    if origin and origin in _allowed_origins():
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, DELETE",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
        }
    return {}


def _auth_disabled() -> bool:
    return os.getenv("CV_AGENT_AUTH_DISABLED", "false").lower() in (
        "1", "true", "yes",
    )


def _verify_token(token: str) -> str:
    import jwt

    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise ValueError("JWT_SECRET is not configured on CV Agent.")

    payload = jwt.decode(token, secret, algorithms=["HS256"])
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token: missing sub claim.")
    return str(sub)


def register_jwt_middleware(app: "FastAPI") -> None:
    from starlette.responses import JSONResponse

    @app.middleware("http")
    async def jwt_auth_middleware(request: Request, call_next):
        if _auth_disabled():
            return await call_next(request)

        path = request.url.path
        if path in _PUBLIC_PATHS or path.startswith("/health"):
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized — Bearer token required."},
                headers=_cors_headers(request),
            )

        token = header[7:].strip()
        try:
            request.state.user_id = _verify_token(token)
        except Exception as exc:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid or expired token: {exc}"},
                headers=_cors_headers(request),
            )

        return await call_next(request)
