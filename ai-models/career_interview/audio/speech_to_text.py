"""
speech_to_text.py
=================
Transcribes audio files to text using one of two Whisper backends:

  1. LOCAL  — openai-whisper (runs on-device, no API key needed beyond setup)
  2. CLOUD  — OpenAI Whisper API (whisper-1, requires OPENAI_API_KEY)

The backend is selected via Config.WHISPER_BACKEND ("local" | "cloud" | "auto").
In "auto" mode (the default) the system tries local first, and if the model
weights are unavailable it silently falls back to the cloud API.

Supported input formats: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg, flac
"""

import os
import json
import subprocess
import tempfile
from typing import Optional

from config import Config


# ---------------------------------------------------------------------------
# Validation helper (uses ffprobe)
# ---------------------------------------------------------------------------

def _validate_audio(path: str) -> dict:
    """
    Uses ffprobe to confirm the file contains a valid audio stream.

    Returns a dict with 'duration', 'codec', 'sample_rate' keys.
    Raises RuntimeError if the file has no audio stream or is unreadable.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe could not read file '{path}': {result.stderr.strip()}"
        )

    info = json.loads(result.stdout)
    audio_streams = [
        s for s in info.get("streams", [])
        if s.get("codec_type") == "audio"
    ]
    if not audio_streams:
        raise RuntimeError(
            f"File '{path}' contains no audio stream. "
            "Make sure it is a valid audio/video file."
        )

    fmt = info.get("format", {})
    a = audio_streams[0]
    return {
        "duration": float(fmt.get("duration", 0)),
        "codec": a.get("codec_name"),
        "sample_rate": int(a.get("sample_rate", 0)),
        "channels": int(a.get("channels", 1)),
    }


# ---------------------------------------------------------------------------
# Pre-processing: normalise audio to 16 kHz mono WAV for Whisper
# ---------------------------------------------------------------------------

def _normalise_to_wav(src: str, dst: str) -> None:
    """
    Converts any audio/video file to a 16 kHz, mono, 16-bit WAV.
    Uses explicit PCM codec — critical for browser webm/opus recordings where
    ffmpeg may silently produce an unreadable file without -acodec pcm_s16le.
    Falls back to stripping video stream if the first attempt fails.
    """
    def _run_ffmpeg(extra_flags: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", src,
            ] + extra_flags + [
                "-ar", "16000",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                dst,
            ],
            capture_output=True,
            text=True,
        )

    # First attempt — straightforward conversion
    result = _run_ffmpeg([])
    if result.returncode == 0:
        return

    # Second attempt — strip video stream (some browser webm containers confuse ffmpeg)
    result2 = _run_ffmpeg(["-vn"])
    if result2.returncode == 0:
        return

    raise RuntimeError(
        f"ffmpeg normalisation failed for '{src}': {result.stderr.strip()}"
    )



# ---------------------------------------------------------------------------
# Backend 1 — Local Whisper
# ---------------------------------------------------------------------------

_local_model_cache: dict = {}


def _transcribe_local(wav_path: str, model_name: str = "base") -> str:
    """
    Transcribes using the locally installed openai-whisper package.
    The model weights are cached after the first load.

    Raises ImportError if openai-whisper is not installed.
    Raises RuntimeError if the model weights cannot be downloaded (offline env).
    """
    try:
        import whisper  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "openai-whisper is not installed. "
            "Run: pip install openai-whisper"
        ) from exc

    if model_name not in _local_model_cache:
        _local_model_cache[model_name] = whisper.load_model(model_name)

    model = _local_model_cache[model_name]
    result = model.transcribe(wav_path, fp16=False)
    # Empty string is valid — silence or non-speech audio produces no output.
    # We return it as-is; callers decide whether an empty answer is acceptable.
    return result.get("text", "").strip()


# ---------------------------------------------------------------------------
# Backend 2 — OpenAI Cloud Whisper API
# ---------------------------------------------------------------------------

def _transcribe_cloud(wav_path: str) -> str:
    """
    Transcribes using the OpenAI Whisper API (whisper-1).
    Requires a valid OPENAI_API_KEY in the environment / Config.
    """
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "openai package is not installed. "
            "Run: pip install openai"
        ) from exc

    api_key = Config.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Cannot use cloud Whisper without an API key."
        )

    client = OpenAI(api_key=api_key)

    with open(wav_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )

    # response is a plain string when response_format="text"
    # Empty string is valid for silence/non-speech — callers handle it.
    return str(response).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transcribe_audio(
    file_path: str,
    backend: Optional[str] = None,
) -> str:
    """
    Transcribes an audio file to text.

    Args:
        file_path: Path to the audio file (mp3, wav, mp4, m4a, webm, etc.)
        backend:   Override Config.WHISPER_BACKEND.
                   "local"  — use on-device Whisper model
                   "cloud"  — use OpenAI Whisper API
                   "auto"   — try local first; only fall back to cloud on a
                              hard failure (import error, model load error),
                              NOT on an empty result (silence is valid).

    Returns:
        Transcribed text as a string (may be empty for silent audio).

    Raises:
        FileNotFoundError: File does not exist.
        RuntimeError:      File has no audio stream, or all backends fail.
    """
    selected_backend = (backend or getattr(Config, "WHISPER_BACKEND", "auto")).lower()

    # ── 1. Validate the input file ─────────────────────────────────────────
    _validate_audio(file_path)  # raises on invalid file

    # ── 2. Normalise to 16 kHz mono WAV ────────────────────────────────────
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        _normalise_to_wav(file_path, wav_path)

        # ── 2b. Energy pre-check — detect truly silent recordings early ────
        # Browser webm/opus sometimes converts to a valid WAV with near-zero
        # signal (mic muted, permissions denied). Detect this before Whisper.
        try:
            import wave, struct, math
            with wave.open(wav_path, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            if raw:
                samples = struct.unpack(f"{len(raw)//2}h", raw[:len(raw) - len(raw)%2])
                rms = math.sqrt(sum(s*s for s in samples) / max(len(samples), 1))
                if rms < 50:  # 50/32768 ≈ 0.15% max amplitude — truly silent
                    return ""
        except Exception:
            pass  # energy check failed — let Whisper decide

        # ── 3. Transcribe ──────────────────────────────────────────────────
        if selected_backend == "local":
            return _transcribe_local(wav_path, getattr(Config, "WHISPER_MODEL", "base"))

        if selected_backend == "cloud":
            return _transcribe_cloud(wav_path)

        # "auto" — try local; fall back to cloud ONLY on import/load errors,
        # not on empty transcriptions (silence is a valid result, not a failure).
        try:
            return _transcribe_local(wav_path, getattr(Config, "WHISPER_MODEL", "base"))
        except ImportError as local_err:
            # openai-whisper not installed — try cloud
            print(
                f"[speech_to_text] Local Whisper unavailable ({local_err}). "
                "Falling back to OpenAI cloud API..."
            )
        except Exception as local_err:
            # Model download failed, GPU error, etc. — try cloud
            print(
                f"[speech_to_text] Local Whisper failed ({local_err}). "
                "Falling back to OpenAI cloud API..."
            )

        # Cloud fallback
        try:
            return _transcribe_cloud(wav_path)
        except ImportError:
            raise RuntimeError(
                "Neither openai-whisper nor the openai package is installed.\n"
                "Fix with:  pip install openai-whisper openai"
            )

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


# ---------------------------------------------------------------------------
# Standalone test helper
# ---------------------------------------------------------------------------

def test_pipeline(audio_path: str) -> None:
    """Quick smoke-test: validates and transcribes a given audio file."""
    print(f"\n[test] Validating: {audio_path}")
    info = _validate_audio(audio_path)
    print(f"  duration   : {info['duration']:.1f}s")
    print(f"  codec      : {info['codec']}")
    print(f"  sample_rate: {info['sample_rate']} Hz")
    print(f"  channels   : {info['channels']}")

    print("[test] Transcribing...")
    text = transcribe_audio(audio_path)
    print(f"  result: {text!r}")



# ---------------------------------------------------------------------------
# Technical term correction — fixes common Whisper mishearings
# ---------------------------------------------------------------------------

# Static map: (wrong phonetic → correct term)
TECH_TERM_CORRECTIONS = {
    # ML frameworks
    "by touch": "PyTorch", "pie torch": "PyTorch", "pi torch": "PyTorch",
    "pie touch": "PyTorch", "pytorge": "PyTorch", "pytorch": "PyTorch",
    "tensor flow": "TensorFlow", "tensorflow": "TensorFlow",
    "tensor fore": "TensorFlow", "tensor flo": "TensorFlow",
    "sai kit learn": "scikit-learn", "scikit learn": "scikit-learn",
    "sky kit learn": "scikit-learn", "psychic learn": "scikit-learn",
    "hugging face": "HuggingFace", "hugging faces": "HuggingFace",
    # AI/ML terms
    "elle em": "LLM", "el el em": "LLM",
    "elle em m": "LLM", "large language model": "LLM",
    "rag": "RAG", "retrieval augmented generation": "RAG",
    "open a i": "OpenAI", "open ai": "OpenAI",
    "g p t": "GPT", "gpt for": "GPT-4", "gpt three": "GPT-3",
    "bert": "BERT", "roberta": "RoBERTa",
    "lang chain": "LangChain", "lane chain": "LangChain",
    "lang graph": "LangGraph",
    "fast a p i": "FastAPI", "fast api": "FastAPI",
    "my sequel": "MySQL", "my s q l": "MySQL",
    "post gres": "PostgreSQL", "postgres": "PostgreSQL",
    "mongo d b": "MongoDB", "mongo db": "MongoDB",
    "redis": "Redis", "elastic search": "Elasticsearch",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "K8s",
    "git hub": "GitHub", "git lab": "GitLab",
    "amazon s3": "Amazon S3", "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "jupiter": "Jupyter", "jupiter notebook": "Jupyter Notebook",
    "pie thon": "Python", "python": "Python",
    "java script": "JavaScript", "type script": "TypeScript",
    "react j s": "ReactJS", "node j s": "NodeJS",
    "sequel": "SQL", "nosql": "NoSQL",
    "a p i": "API", "apis": "APIs",
    "r n n": "RNN", "l s t m": "LSTM", "c n n": "CNN",
    "g a n": "GAN", "gans": "GANs",
    "n l p": "NLP", "c v": "CV", "a i": "AI", "m l": "ML",
    "b e r t": "BERT", "g p u": "GPU", "c p u": "CPU",
    "vector d b": "VectorDB", "pinecone": "Pinecone",
    "chroma": "Chroma", "weaviate": "Weaviate",
    "whisper": "Whisper", "open c v": "OpenCV", "opencv": "OpenCV",
    "numpy": "NumPy", "pandas": "Pandas", "matplotlib": "Matplotlib",
    "scikit": "scikit", "scipy": "SciPy",
}

def _build_context_corrections(context_text: str) -> dict:
    """
    Extract technical terms from CV/JD context and build phonetic corrections.
    Handles camelCase, acronyms, and compound words.
    """
    import re
    corrections = {}
    # Find capitalized technical terms (CamelCase, ALLCAPS, version numbers)
    terms = re.findall(r'\b[A-Z][a-zA-Z0-9]+(?:[A-Z][a-z]+)*\b|\b[A-Z]{2,10}\b', context_text)
    for term in set(terms):
        if len(term) < 2:
            continue
        # Add lowercase version as a key
        corrections[term.lower()] = term
        # Add space-separated version for compound words
        spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', term).lower()
        if spaced != term.lower():
            corrections[spaced] = term
    return corrections


def correct_technical_terms(transcript: str, context: str = "") -> str:
    """
    Post-process Whisper transcript to fix common technical term mishearings.
    Uses both a static correction map and context-aware dynamic corrections.

    Args:
        transcript: Raw Whisper output
        context:    CV text + JD text to extract expected technical terms from

    Returns:
        Corrected transcript string
    """
    import re
    if not transcript:
        return transcript

    # Build combined correction map (static + dynamic from context)
    all_corrections = dict(TECH_TERM_CORRECTIONS)
    if context:
        all_corrections.update(_build_context_corrections(context))

    result = transcript

    # Apply corrections — longest match first to avoid partial substitutions
    for wrong, right in sorted(all_corrections.items(), key=lambda x: -len(x[0])):
        # Case-insensitive word-boundary match
        pattern = r'(?i)\b' + re.escape(wrong) + r'\b'
        result = re.sub(pattern, right, result)

    return result.strip()


# ---------------------------------------------------------------------------
# Transcript cleanup pipeline
# ---------------------------------------------------------------------------

FILLER_PATTERNS = [
    r'\b(um+|uh+|er+|ah+)\b',
    r'\byou know\b',
    r'\bI mean\b',
    r'\blike,?\s+(?=\w)',      # "like" as filler before words
    r'\bkind of\b',
    r'\bsort of\b',
    r'\bbasically\b',
    r'\bliterally\b',
    r'\bactually,\b',
    r'\bright\?\s*',
    r'\bokay so\b',
    r'\bso+,?\s+(?=[A-Z])',    # sentence-starting "So..."
]

def clean_transcript(text: str) -> str:
    """
    Clean a Whisper transcript for evaluation:
    - Remove filler words
    - Fix punctuation spacing
    - Normalize whitespace
    - Capitalize sentences
    """
    import re
    if not text:
        return text

    cleaned = text

    # Remove filler patterns
    for pattern in FILLER_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

    # Fix multiple spaces
    cleaned = re.sub(r' {2,}', ' ', cleaned)

    # Fix spacing around punctuation
    cleaned = re.sub(r'\s+([.,?!])', r'\1', cleaned)
    cleaned = re.sub(r'([.,?!])(?=[A-Za-z])', r'\1 ', cleaned)

    # Capitalize after sentence-ending punctuation
    cleaned = re.sub(r'([.!?])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), cleaned)

    # Capitalize first letter
    cleaned = cleaned.strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned.strip()
