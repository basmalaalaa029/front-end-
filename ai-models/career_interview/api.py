"""
api.py — Production-grade FastAPI backend.
Fixes: rate limiting, retry logic, duplicate prevention, token optimization,
proper error handling, file validation, request queuing, logging.
"""
import os, uuid, shutil, threading, wave, io, time, logging, asyncio, hashlib
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
import main as interview
from config import Config

_PKG_ROOT = Path(__file__).resolve().parent
_LOG_FILE = _PKG_ROOT / "interview_system.log"

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(_LOG_FILE), encoding="utf-8"),
    ],
)
log = logging.getLogger("interview")

# ── In-flight request tracker (prevents duplicate submissions) ────────────
_in_flight: set = set()
_in_flight_lock = threading.Lock()

# ── Piper TTS (zip default: ~/piper-voices/en_US-lessac-medium.onnx) ───────
def _piper_model_path() -> str:
    from config import Config
    return os.path.expanduser(
        getattr(Config, "PIPER_MODEL_PATH", "")
        or os.getenv("PIPER_MODEL_PATH", "~/piper-voices/en_US-lessac-medium.onnx")
    )

_piper_voice = None
_tts_lock = threading.Lock()

try:
    from piper.voice import PiperVoice
    _PIPER_AVAILABLE = True
except ImportError:
    PiperVoice = None  # type: ignore[misc, assignment]
    _PIPER_AVAILABLE = False

def _piper_model_ready() -> bool:
    path = _piper_model_path()
    return os.path.isfile(path) and os.path.isfile(path + ".json")

def _get_voice():
    global _piper_voice
    if not _PIPER_AVAILABLE:
        raise RuntimeError("piper-tts is not installed")
    model_path = _piper_model_path()
    if not _piper_model_ready():
        raise FileNotFoundError(
            f"Piper voice not found at {model_path}. "
            "Run: bash scripts/install_piper_voice.sh"
        )
    if _piper_voice is None:
        _piper_voice = PiperVoice.load(model_path)
    return _piper_voice

def _synth_to_wav(text: str) -> bytes:
    with _tts_lock:
        voice = _get_voice()
        buf = io.BytesIO()
        wav = wave.open(buf, "wb")
        try:
            voice.synthesize_wav(text, wav)
        finally:
            wav.close()
        data = buf.getvalue()
        if len(data) < 44:
            raise RuntimeError("Piper produced empty audio — check espeak-ng is installed")
        return data

# ── Retry with exponential backoff ────────────────────────────────────────
def _with_retry(fn, *args, max_retries=3, base_delay=1.0, **kwargs):
    """Call fn with exponential backoff on Groq rate-limit or transient errors."""
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate" in err_str or "429" in err_str or "quota" in err_str
            is_transient = "timeout" in err_str or "connection" in err_str or "503" in err_str
            if (is_rate_limit or is_transient) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                log.warning(f"Attempt {attempt+1} failed ({e}). Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("Max retries exceeded")

# ── File validation ───────────────────────────────────────────────────────
MAX_FILE_MB = 10
ALLOWED_EXTS = {".pdf"}

def _validate_upload(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"Only PDF files are supported. Got: {file.filename}")
    if file.size and file.size > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {MAX_FILE_MB}MB.")

# ── User-friendly error messages ──────────────────────────────────────────
def _friendly_error(e: Exception) -> str:
    msg = str(e).lower()
    if "rate" in msg or "429" in msg or "quota" in msg:
        return "The AI service is temporarily busy. Please wait a moment and try again."
    if "timeout" in msg or "connection" in msg:
        return "Connection timeout. Please check your internet and try again."
    if "api key" in msg or "authentication" in msg or "401" in msg:
        return "API key error. Please check your .env configuration."
    if "pdf" in msg or "parse" in msg:
        return "Could not read your PDF. Please ensure it contains selectable text (not a scanned image)."
    if "no module" in msg:
        return "A required package is missing. Please run: pip install -r requirements.txt"
    return f"Something went wrong: {str(e)[:120]}"

# Simple = cache for /speak
_tts_cache: dict = {}
_TTS_CACHE_MAX = 10


def register_career_interview_routes(app: FastAPI) -> None:
    """Register career interview API routes on the shared CV Agent FastAPI app."""

    def _frontend_base() -> str:
        return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    @app.get("/")
    def legacy_interview_ui_redirect():
        """Interview UI lives on the frontend — not on the API server."""
        return RedirectResponse(
            url=f"{_frontend_base()}/dashboard/interview",
            status_code=302,
        )

    @app.get("/recruiter")
    def legacy_recruiter_ui_redirect():
        return RedirectResponse(
            url=f"{_frontend_base()}/interview/recruiter.html",
            status_code=302,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": _friendly_error(exc)},
        )

    @app.post("/session/{user_id}/finish_early")
    async def finish_early(user_id: str):
        """End session immediately — run final evaluation on answered questions only."""
        from main import _sessions, _serialize_turns
        from graph.nodes import generate_final_eval, end_interview
        s = _sessions.get(user_id)
        if not s:
            raise HTTPException(404, "Session not found")
        s = dict(s)
        s["early_finished"] = True
        s["session_complete"] = True
        s["interview_complete"] = True
        turns_snapshot = list(s.get("turns", []))
        loop = asyncio.get_event_loop()
        try:
            fe = await loop.run_in_executor(None, generate_final_eval, s)
            s = {**s, **fe}
        except Exception as e:
            log.error(f"finish_early final_eval error: {e}", exc_info=True)
        if not s.get("turns"):
            s["turns"] = turns_snapshot
        try:
            s = {**s, **end_interview(s)}
        except Exception as e:
            log.error(f"finish_early end_interview error: {e}")
        _sessions[user_id] = s
        ev = s.get("final_evaluation") or {}
        turns = s.get("turns", [])
        return {
            "status": "success",
            "interview_complete": True,
            "early_finished": True,
            "final_evaluation": ev,
            "all_turns": _serialize_turns(turns),
            "topics_covered": s.get("topics_covered", []),
            "mode": s.get("interview_mode", "text"),
            "questions_asked": s.get("questions_asked", 0),
            "end_reason": "early_finish",
        }

    @app.get("/session/{user_id}")
    async def get_session(user_id: str):
        """Check if a session is still alive (for resume after refresh)."""
        sessions = interview.get_sessions()
        if user_id not in sessions:
            raise HTTPException(404, "Session not found or expired.")
        s = sessions[user_id]
        turns = s.get("turns", [])
        result = {
            "status": "active",
            "user_id": user_id,
            "questions_asked": s.get("questions_asked", 0),
            "current_question": s.get("current_question", ""),
            "interview_complete": s.get("interview_complete", False),
            "level": s.get("level", "mid"),
            "role_label": s.get("role_label", "Professional"),
            "interview_phase": s.get("interview_phase", "technical"),
            "last_turn": turns[-1] if turns else None,
            "interview_mode": s.get("interview_mode", "text"),
            "main_question_index": s.get("main_question_index", 0),
        }
        if s.get("interview_complete"):
            if not s.get("final_evaluation"):
                try:
                    from graph.nodes import generate_final_eval
                    fe_result = generate_final_eval(s)
                    s = {**s, **fe_result}
                    sessions[user_id] = s
                    log.info(f"Re-ran final eval on session recovery for user={user_id}")
                except Exception as e:
                    log.error(f"Session recovery final eval failed: {e}")
            result["final_evaluation"] = s.get("final_evaluation") or {}
            result["all_turns"] = interview._serialize_turns(turns)
            result["topics_covered"] = s.get("topics_covered", [])
            result["questions_asked"] = s.get("questions_asked", 0)
        return result

    @app.get("/results/{user_id}")
    async def get_results(user_id: str):
        """Fetch complete evaluation results for a finished session. Re-runs eval if missing."""
        sessions = interview.get_sessions()
        if user_id not in sessions:
            raise HTTPException(404, "Session not found or expired.")
        s = sessions[user_id]
        if not s.get("interview_complete"):
            raise HTTPException(400, "Interview not yet complete.")
        turns = s.get("turns", [])
        if not s.get("final_evaluation"):
            try:
                from graph.nodes import generate_final_eval
                fe_result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: generate_final_eval(s)
                )
                s = {**s, **fe_result}
                sessions[user_id] = s
                log.info(f"Re-ran final eval for results endpoint user={user_id}")
            except Exception as e:
                log.error(f"Results endpoint final eval failed: {e}")
        ev = s.get("final_evaluation") or {}
        return {
            "status": "complete",
            "final_evaluation": ev,
            "all_turns": interview._serialize_turns(turns),
            "topics_covered": s.get("topics_covered", []),
            "questions_asked": s.get("questions_asked", 0),
            "interview_mode": s.get("interview_mode", "text"),
            "candidate_name": s.get("candidate_name", ""),
            "role_label": s.get("role_label", ev.get("role_label", "")),
        }

    @app.post("/speak")
    async def speak(text: str = Form(...)):
        if not text.strip():
            raise HTTPException(400, "Text is empty.")
        text = text[:600].strip()
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in _tts_cache:
            audio_bytes = _tts_cache[cache_key]
            log.debug(f"TTS cache hit for: {text[:40]}...")
            return StreamingResponse(
                iter([audio_bytes]),
                media_type="audio/wav",
                headers={"Content-Length": str(len(audio_bytes)), "X-TTS-Cache": "hit"},
            )
        loop = asyncio.get_event_loop()
        try:
            audio_bytes = await loop.run_in_executor(None, _synth_to_wav, text)
            if len(_tts_cache) >= _TTS_CACHE_MAX:
                oldest = next(iter(_tts_cache))
                del _tts_cache[oldest]
            _tts_cache[cache_key] = audio_bytes
            return StreamingResponse(
                iter([audio_bytes]),
                media_type="audio/wav",
                headers={"Content-Length": str(len(audio_bytes))},
            )
        except FileNotFoundError as e:
            log.error(f"TTS model missing: {e}")
            raise HTTPException(
                503,
                "Voice model not installed. Run: cd ai-models && bash scripts/install_piper_voice.sh",
            )
        except RuntimeError as e:
            log.error(f"TTS error: {e}")
            msg = str(e)
            if "piper-tts" in msg.lower():
                raise HTTPException(503, "piper-tts is not installed. Run: pip install piper-tts")
            raise HTTPException(500, "Voice synthesis failed.")
        except Exception as e:
            log.error(f"TTS error: {e}")
            raise HTTPException(500, "Voice synthesis failed.")

    @app.post("/start")
    async def start(
        file: UploadFile = File(...),
        interview_mode: str = Form("text"),
        job_description: str = Form(""),
    ):
        if not Config.GROQ_API_KEY.startswith("gsk_"):
            raise HTTPException(
                503,
                "GROQ_API_KEY is missing or invalid. Add your key from https://console.groq.com "
                "to ai-models/.env (GROQ_API_KEY=gsk_...) and restart the server.",
            )
        _validate_upload(file)
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        path = f"{Config.UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"

        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if not os.path.exists(path) or os.path.getsize(path) < 100:
            raise HTTPException(400, "Uploaded file appears to be empty or corrupt.")

        log.info(f"Starting session: mode={interview_mode}, file={file.filename}, jd_len={len(job_description)}")
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _with_retry(
                    interview.start_session,
                    path,
                    interview_mode=interview_mode,
                    job_description=job_description,
                ),
            )
        except Exception as e:
            log.error(f"start_session failed: {e}", exc_info=True)
            raise HTTPException(500, _friendly_error(e))

        if result.get("status") == "error":
            raise HTTPException(400, result["message"])

        log.info(
            f"Session started: user={result.get('user_id','?')}, "
            f"role={result.get('role_label','?')}, level={result.get('level','?')}, "
            f"mode={interview_mode}, competencies={len(result.get('competency_plan',[]))}"
        )
        return result

    @app.post("/answer/text")
    async def answer_text(
        user_id: str = Form(...),
        answer: str = Form(...),
        is_practice: str = Form("false"),
    ):
        if not answer.strip():
            raise HTTPException(400, "Answer cannot be empty.")
        if len(answer) > 5000:
            answer = answer[:5000]
        practice = is_practice.lower() in ("true", "1", "yes")

        key = f"text:{user_id}"
        with _in_flight_lock:
            if key in _in_flight:
                raise HTTPException(429, "Your previous answer is still being processed. Please wait.")
            _in_flight.add(key)

        try:
            log.info(f"Text answer: user={user_id}, len={len(answer)}, words={len(answer.split())}, practice={practice}")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _with_retry(interview.submit_answer, user_id, answer=answer, is_practice=practice),
            )
        except Exception as e:
            log.error(f"submit_answer failed: {e}", exc_info=True)
            raise HTTPException(500, _friendly_error(e))
        finally:
            with _in_flight_lock:
                _in_flight.discard(key)

        if result.get("status") == "error":
            raise HTTPException(400, result["message"])
        if result.get("interview_complete"):
            ev = result.get("final_evaluation") or {}
            log.info(
                f"Interview complete: user={user_id}, score={ev.get('overall_score','?')}, "
                f"rec={ev.get('hiring_recommendation','?')}, turns={result.get('questions_asked','?')}"
            )
        else:
            log.info(
                f"Answer processed: user={user_id}, turn={result.get('turn','?')}, "
                f"main_q={result.get('main_question_index','?')}, phase={result.get('interview_phase','?')}, "
                f"action={result.get('next_action','?')}"
            )
        return result

    @app.post("/answer/audio")
    async def answer_audio(
        user_id: str = Form(...),
        file: UploadFile = File(...),
        is_practice: str = Form("false"),
    ):
        practice = is_practice.lower() in ("true", "1", "yes")
        key = f"audio:{user_id}"
        with _in_flight_lock:
            if key in _in_flight:
                raise HTTPException(429, "Still processing your previous recording. Please wait.")
            _in_flight.add(key)

        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[-1] or ".webm"
        path = f"{Config.UPLOAD_DIR}/audio_{uuid.uuid4()}{ext}"

        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            log.info(f"Audio answer: user={user_id}, file={path}, practice={practice}")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _with_retry(interview.submit_answer, user_id, media_file_path=path, is_practice=practice),
            )
        except Exception as e:
            log.error(f"audio answer failed: {e}", exc_info=True)
            raise HTTPException(500, _friendly_error(e))
        finally:
            with _in_flight_lock:
                _in_flight.discard(key)
            if os.path.exists(path):
                os.remove(path)

        if result.get("status") == "error":
            raise HTTPException(400, result["message"])
        return result

    @app.post("/answer/video")
    async def answer_video(
        user_id: str = Form(...),
        file: UploadFile = File(...),
        is_practice: str = Form("false"),
    ):
        practice = is_practice.lower() in ("true", "1", "yes")
        key = f"video:{user_id}"
        with _in_flight_lock:
            if key in _in_flight:
                raise HTTPException(429, "Still processing your previous recording. Please wait.")
            _in_flight.add(key)

        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[-1] or ".webm"
        path = f"{Config.UPLOAD_DIR}/video_{uuid.uuid4()}{ext}"

        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            log.info(f"Video answer: user={user_id}, file={path}, practice={practice}")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _with_retry(interview.submit_answer, user_id, media_file_path=path, is_practice=practice),
            )
        except Exception as e:
            log.error(f"video answer failed: {e}", exc_info=True)
            raise HTTPException(500, _friendly_error(e))
        finally:
            with _in_flight_lock:
                _in_flight.discard(key)
            if os.path.exists(path):
                os.remove(path)

        if result.get("status") == "error":
            raise HTTPException(400, result["message"])
        return result

    @app.post("/transcribe")
    async def transcribe_only(file: UploadFile = File(...)):
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[-1] or ".webm"
        path = f"{Config.UPLOAD_DIR}/preview_{uuid.uuid4()}{ext}"
        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            transcript = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _transcribe_preview(path),
            )
            return {"transcript": transcript}
        except Exception as e:
            log.warning(f"Preview transcription failed: {e}")
            return {"transcript": ""}
        finally:
            if os.path.exists(path):
                os.remove(path)

    @app.post("/dataset/upload")
    async def upload_dataset(
        user_id: str = Form(...),
        file: UploadFile = File(...),
    ):
        from chains.dataset_scorer import save_custom_dataset
        import json as _json
        import csv as _csv
        import io as _io

        ext = os.path.splitext(file.filename or "")[-1].lower()
        content = await file.read()

        entries = []
        try:
            if ext == ".json":
                entries = _json.loads(content.decode("utf-8"))
                if not isinstance(entries, list):
                    raise HTTPException(400, "JSON must be an array of objects.")
            elif ext in (".csv", ".tsv"):
                sep = "\t" if ext == ".tsv" else ","
                reader = _csv.DictReader(_io.StringIO(content.decode("utf-8")), delimiter=sep)
                for row in reader:
                    entry = {
                        "competency": row.get("competency", "general"),
                        "question_keywords": [k.strip() for k in row.get("question_keywords", "").split(";") if k.strip()],
                        "ideal_answer": row.get("ideal_answer", ""),
                        "key_concepts": [k.strip() for k in row.get("key_concepts", "").split(";") if k.strip()],
                    }
                    entries.append(entry)
            else:
                raise HTTPException(400, "Only .json, .csv, or .tsv files are supported.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Could not parse file: {e}")

        ok, msg = save_custom_dataset(user_id, entries)
        if not ok:
            raise HTTPException(400, msg)

        sessions = interview.get_sessions()
        if user_id in sessions:
            from chains.dataset_scorer import load_dataset, precompute_dataset_embeddings
            from config import Config as _Cfg
            s = sessions[user_id]
            try:
                raw = load_dataset(s.get("role", "other"), user_id=user_id)
                s["dataset_entries"] = precompute_dataset_embeddings(
                    raw, getattr(_Cfg, "OLLAMA_BASE_URL", "http://localhost:11434")
                )
                log.info(f"Dataset hot-reloaded for user={user_id}: {len(s['dataset_entries'])} entries")
            except Exception as e:
                log.warning(f"Hot-reload failed: {e}")

        log.info(f"Custom dataset uploaded: user={user_id}, entries={len(entries)}")
        return {"status": "ok", "entries_saved": len(entries), "message": msg}

    @app.get("/dataset/info/{user_id}")
    async def dataset_info(user_id: str):
        sessions = interview.get_sessions()
        entries = []
        if user_id in sessions:
            entries = sessions[user_id].get("dataset_entries", [])

        return {
            "total_entries": len(entries),
            "has_custom": any(e.get("source") == "custom" for e in entries),
            "competencies_covered": list(set(e.get("competency", "") for e in entries)),
            "embedding_method": "ollama/nomic-embed-text",
            "blend_weights": {"llm": 0.65, "dataset": 0.35},
        }

    @app.get("/recruiter/sessions")
    async def get_recruiter_sessions():
        sessions = interview.get_sessions()
        result = []
        for uid, s in sessions.items():
            if not s.get("interview_complete"):
                continue
            ev = s.get("final_evaluation") or {}
            turns = s.get("turns", [])
            result.append({
                "session_id": uid,
                "candidate_name": s.get("candidate_name", "Anonymous"),
                "role_label": s.get("role_label", ev.get("role_label", "—")),
                "level": s.get("level", "mid"),
                "overall_score": ev.get("overall_score"),
                "technical_average": ev.get("technical_average"),
                "hiring_recommendation": ev.get("hiring_recommendation"),
                "role_fit_score": ev.get("role_fit_score"),
                "readiness": ev.get("readiness"),
                "competency_scores": ev.get("competency_scores", {}),
                "soft_skills": ev.get("soft_skills", {}),
                "strengths": ev.get("strengths", []),
                "weak_areas": ev.get("weak_areas", []),
                "summary_paragraph": ev.get("summary_paragraph", ""),
                "hiring_rationale": ev.get("hiring_rationale", ""),
                "interview_consistency": ev.get("interview_consistency", "stable"),
                "growth_potential": ev.get("growth_potential", "medium"),
                "mentorship_need": ev.get("mentorship_need", ""),
                "bluff_assessment": ev.get("bluff_assessment", ""),
                "all_turns": [
                    {
                        "turn": t.get("turn"),
                        "question": t.get("question"),
                        "answer": t.get("answer"),
                        "score": float(t.get("score") or 0),
                        "feedback": t.get("feedback"),
                        "is_followup": t.get("is_followup"),
                        "competency_tag": t.get("competency_tag"),
                        "question_category": t.get("question_category"),
                    }
                    for t in turns
                ],
                "questions_asked": s.get("questions_asked", 0),
                "completed": True,
                "timestamp": s.get("timestamp", None),
                "interview_mode": s.get("interview_mode", "text"),
            })
        result.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
        return result

    @app.post("/recruiter/note/{session_id}")
    async def save_recruiter_note(
        session_id: str,
        note: str = Form(""),
        override_score: str = Form(""),
        override_rec: str = Form(""),
    ):
        sessions = interview.get_sessions()
        if session_id not in sessions:
            raise HTTPException(404, "Session not found.")
        s = sessions[session_id]
        if note:
            s["recruiter_note"] = note
        if override_score:
            try:
                s["recruiter_score"] = float(override_score)
            except ValueError:
                pass
        if override_rec:
            s["recruiter_rec"] = override_rec
        s["recruiter_updated"] = True
        log.info(f"Recruiter note saved: session={session_id}, override_rec={override_rec or 'none'}")
        return {"status": "ok"}

    @app.post("/session/{user_id}/name")
    async def set_candidate_name(user_id: str, name: str = Form(...)):
        sessions = interview.get_sessions()
        if user_id in sessions:
            sessions[user_id]["candidate_name"] = name[:100]
        return {"status": "ok"}


def _transcribe_preview(path: str) -> str:
    """Transcribe audio for preview — no scoring, no state changes."""
    try:
        from audio.speech_to_text import transcribe_audio, correct_technical_terms
        transcript = transcribe_audio(path)
        if transcript:
            transcript = correct_technical_terms(transcript)
        return transcript or ""
    except Exception as e:
        log.warning(f"_transcribe_preview error: {e}")
        return ""
