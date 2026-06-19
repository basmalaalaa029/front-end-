"""
main.py
=======
Entry point for the CV Agent API server.

Development:
    python3 main.py

Production:
    gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 300
"""

import os

from load_env import load_env

load_env()

from cv_agent.app.api import app  # noqa: E402 — must load after dotenv

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
