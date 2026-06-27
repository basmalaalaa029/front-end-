import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from load_env import sanitize_api_key
except ImportError:
    def sanitize_api_key(value: str) -> str:
        if not value:
            return ""
        cleaned = (
            value.strip()
            .replace("\ufeff", "")
            .replace("\u2014", "-")
            .replace("\u2013", "-")
        )
        return cleaned.encode("ascii", "ignore").decode("ascii")

class Config:
    # ── Groq ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: str    = sanitize_api_key(os.getenv("GROQ_API_KEY", ""))
    LLM_MODEL_NAME: str  = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
    TEMPERATURE: float   = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    # ── Embeddings (Ollama — Groq has no embedding API) ───────────────────
    EMBEDDING_MODEL: str    = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_BASE_URL: str    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ── Piper TTS (same path as zip) ──────────────────────────────────────
    PIPER_MODEL_PATH: str = os.getenv(
        "PIPER_MODEL_PATH", "~/piper-voices/en_US-lessac-medium.onnx"
    )

    # ── Whisper ───────────────────────────────────────────────────────────
    WHISPER_MODEL: str   = os.getenv("WHISPER_MODEL", "tiny")
    WHISPER_BACKEND: str = os.getenv("WHISPER_BACKEND", "local")

    # ── Storage (paths relative to this package) ──────────────────────────
    _PKG_ROOT: str = os.path.dirname(os.path.abspath(__file__))
    FAISS_INDEX_DIR: str = os.path.join(_PKG_ROOT, "faiss_indexes")
    UPLOAD_DIR: str = os.path.join(_PKG_ROOT, "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

    # ── RAG ───────────────────────────────────────────────────────────────
    CHUNK_SIZE: int    = int(os.getenv("CHUNK_SIZE",    "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    RETRIEVER_K: int   = int(os.getenv("RETRIEVER_K",  "3"))

    # ── Interview flow ────────────────────────────────────────────────────
    FOLLOWUP_SCORE_THRESHOLD: float = float(os.getenv("FOLLOWUP_SCORE_THRESHOLD", "6.0"))
    WEAK_SCORE_THRESHOLD:     float = float(os.getenv("WEAK_SCORE_THRESHOLD",     "5.0"))
    EARLY_STOP_SCORE:  float = float(os.getenv("EARLY_STOP_SCORE",  "3.0"))
    # Raise early stop count so the session doesn't end early for 8-question sessions
    EARLY_STOP_COUNT:  int   = int(os.getenv("EARLY_STOP_COUNT",   "5"))
    MIN_QUESTIONS: int = int(os.getenv("MIN_QUESTIONS", "8"))
    MAX_QUESTIONS: int = int(os.getenv("MAX_QUESTIONS", "8"))
    # Follow-up budget: 3–5 follow-up questions for the whole session (target 4)
    MAX_SESSION_FOLLOWUPS: int = int(os.getenv("MAX_SESSION_FOLLOWUPS", "5"))
    MIN_SESSION_FOLLOWUPS: int = int(os.getenv("MIN_SESSION_FOLLOWUPS", "3"))
    # Max follow-ups per main question (allow up to 2 so budget can concentrate)
    MAX_FOLLOWUPS_PER_QUESTION: int = int(os.getenv("MAX_FOLLOWUPS_PER_QUESTION", "2"))
