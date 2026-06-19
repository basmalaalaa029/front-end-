# CV Agent

Agentic CV generation system using LangGraph, ensemble LLM judges, hallucination detection, and a FastAPI backend. Users choose a tone and fill in their data; the pipeline iteratively refines and scores the CV until it meets quality thresholds, then exports it as a PDF.

## Architecture

```
POST /generate
     │
     ▼
 UserProfile + JD
     │
     ▼
┌────────────────────────────────────────────┐
│              LangGraph Pipeline             │
│                                            │
│  writer_node → judge_node → router_node   │
│       ↑__________________________|         │
│         (loop until score ≥ threshold)     │
└────────────────────────────────────────────┘
     │
     ▼
GET /result/{id}/pdf  →  PDF download
```

**Models used:**
| Role | Model |
|---|---|
| CV Writer | `mistralai/Mistral-7B-Instruct-v0.3` |
| ATS Judge | `OsamaHayba/qwen-ats-merged-stage1` + adapter |
| HR Judge | `Qwen/Qwen2.5-7B-Instruct` |
| Embeddings (RAG) | `sentence-transformers/all-MiniLM-L6-v2` |

---

## Setup

### 1. Clone and install

```bash
cd ai-models
cp env.template .env
./scripts/setup.sh
python scripts/download_gguf.py    # cv-analysis-Q4_K_M.gguf (~4.5 GB)
./scripts/install_llama_server.sh  # prebuilt llama-server → bin/llama-server
./scripts/run.sh
```

**CV analysis** uses a local `llama-server` on port **8080** with `models/gguf/cv-analysis-Q4_K_M.gguf`. First model load can take 30–60s on CPU; judging a CV typically takes 20–90s. Check `/health` — `analysis_ready` should be `true` before analyzing.

If port 8000 is busy: `./scripts/stop.sh && ./scripts/run.sh` (also frees port 8080)

### 2. Configure environment

Edit `ai-models/.env`:

- `HUGGINGFACE_TOKEN` — required for model download
- `JWT_SECRET` — must match `backend/.env`

### 3. Download models (~20 GB, run once)

```bash
.venv/bin/python3 scripts/download_models.py
```

### 4. Verify models load correctly

```bash
.venv/bin/python3 scripts/verify_models.py
```

### 5. Start the server

```bash
./scripts/run.sh
```

Production:

```bash
gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app \
  --bind 0.0.0.0:8000 --timeout 300
```

Open `http://localhost:8000/docs` for the interactive API documentation.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Score a CV vs optional job description (Osama ATS ensemble) |
| `POST` | `/analyze/upload` | Upload PDF/DOCX/TXT and analyze extracted text |
| `POST` | `/generate` | Start CV generation, returns `session_id` |
| `GET` | `/status/{session_id}` | Poll progress |
| `GET` | `/result/{session_id}` | Get final CV (Markdown) + scores |
| `GET` | `/result/{session_id}/pdf` | Download CV as PDF |
| `GET` | `/health` | Server + model status |
| `GET` | `/sessions` | List all active sessions |
| `DELETE` | `/cache` | Clear LLM response cache |

### Example: analyze a CV

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "## Experience\nSenior Engineer at Acme 2020-2024\n- Built APIs serving 2M users",
    "job_description": "Looking for Python, FastAPI, PostgreSQL...",
    "target_role": "Backend Engineer",
    "company": "Acme Corp"
  }'
```

Uses `OsamaHayba/qwen-ats-merged-stage1` + `cv-analysis-final-stage2` when `ANALYSIS_USE_MISTRAL_JUDGE=false` (default). See `notebooks/` for reference notebook; production code is `cv_agent/analysis/service.py`.

### Example: generate a CV

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ahmed Hassan",
    "target_role": "Backend Engineer",
    "tone": "professional",
    "email": "ahmed@example.com",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experiences": ["Senior Dev at Paymob 2021-present: built payment APIs serving 2M users"]
  }'
```

Response:
```json
{ "session_id": "abc123", "status": "pending", "message": "..." }
```

Then poll:
```bash
curl http://localhost:8000/status/abc123
```

Then download the PDF:
```
GET http://localhost:8000/result/abc123/pdf
```

---

## Project Structure

```
ai-models/
├── notebooks/              # Reference notebooks
├── cv_agent/               # Core package (vertical slices)
│   ├── api.py              # FastAPI app + session manager
│   ├── pipeline.py         # LangGraph nodes + runner
│   ├── model_manager.py    # HuggingFace model loading (singleton)
│   ├── analysis/         # 9-layer CV analysis (/analyze)
│   ├── judges.py           # ATS, HR, and rule-based judges
│   ├── routing.py          # Adaptive loop controller
│   ├── hallucination_guard.py  # CV validation against user profile
│   ├── pdf_export.py       # Markdown → PDF with ReportLab
│   ├── rag.py              # FAISS embedding + JD keyword extraction
│   ├── memory.py           # SQLite session store
│   ├── schemas.py          # Pydantic models
│   ├── prompts.py          # Writer & judge system prompts
│   ├── config.py           # PipelineConfig + feature flags
│   ├── cache.py            # Thread-safe LRU cache
│   ├── gpu_queue.py        # Single-threaded GPU worker queue
│   ├── file_parsing.py     # PDF/DOCX/TXT resume parsing
│   └── utils.py            # Shared helpers
├── scripts/
│   ├── download_models.py  # Pre-download HuggingFace models
│   └── verify_models.py    # Test all models load correctly
├── tests/                  # Pytest test suite
├── main.py                 # Server entry point
├── requirements.txt
├── env.template
└── .gitignore
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HUGGINGFACE_TOKEN` | — | Required to download models |
| `WRITER_MODEL` | `mistralai/Mistral-7B-Instruct-v0.3` | CV writer model |
| `JUDGE_BASE_MODEL` | `OsamaHayba/qwen-ats-merged-stage1` | ATS judge base |
| `JUDGE_ADAPTER_PATH` | `OsamaHayba/cv-analysis-final-stage2` | ATS judge LoRA adapter |
| `HR_JUDGE_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | HR judge model |
| `DEVICE` | `auto` | `auto`, `cuda`, `mps`, `cpu` |
| `LOAD_IN_4BIT` | `true` | 4-bit quantization (GPU only) |
| `MAX_ITERATIONS` | `5` | Max pipeline iterations per CV |
| `SCORE_THRESHOLD` | `82` | Target quality score (0–100) |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS allowed origins |
| `RATE_LIMIT_RPM` | `20` | Max requests per minute per IP |
| `PIPELINE_WORKERS` | `2` | Concurrent background workers |

---

## Running Tests

```bash
pytest tests/ -v
```
