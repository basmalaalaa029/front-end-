# Remote GPU inference (Option 3)

Run the **exact fine-tuned HF model** (base + LoRA) on a GPU machine. Your CPU app sends HTTP requests — no 7B model loaded locally.

## Architecture

```
CPU (FastAPI :8000)  ──HTTP──►  GPU (gpu_inference :8080)
                                    qwen-ats-merged-stage1 + cv-analysis-final-stage2
```

## 1. Start the GPU service

On a machine with **CUDA** and **8–16 GB VRAM** (T4 or better):

```bash
cd ai-models
cp env.template .env   # if needed
# Edit .env: set HUGGINGFACE_TOKEN

export HUGGINGFACE_TOKEN=hf_...
export GPU_INFERENCE_API_KEY=my-secret-key   # recommended
chmod +x scripts/run_gpu_inference.sh
./scripts/run_gpu_inference.sh
```

First startup loads the model (~1–3 min). Check:

```bash
curl http://127.0.0.1:8080/health
# {"status":"ok","model_loaded":true,...}
```

### Env vars (GPU side)

| Variable | Default | Description |
|----------|---------|-------------|
| `JUDGE_BASE_MODEL` | `OsamaHayba/qwen-ats-merged-stage1` | Stage-1 merged base |
| `JUDGE_ADAPTER_PATH` | `OsamaHayba/cv-analysis-final-stage2` | Stage-2 LoRA |
| `HUGGINGFACE_TOKEN` | — | HF token for gated/private models |
| `GPU_INFERENCE_API_KEY` | — | Bearer token for clients (optional) |
| `GPU_INFERENCE_PORT` | `8080` | Listen port |
| `LOAD_IN_4BIT` | `true` | 4-bit base (~8 GB VRAM) |
| `GPU_INFERENCE_MAX_NEW_TOKENS` | `1200` | Max generation length |

## 2. Configure the CPU app

In `ai-models/.env` on your **CPU machine**:

```env
CV_ANALYSIS_INFERENCE_MODE=remote
CV_ANALYSIS_LLAMA_SERVER_URL=http://YOUR_GPU_IP:8080
CV_ANALYSIS_REMOTE_API_KEY=my-secret-key
CV_ANALYSIS_REMOTE_HEALTH_TIMEOUT_S=300
CV_ANALYSIS_MOCK_INFERENCE=false
```

Then start the app as usual:

```bash
./scripts/run.sh
```

Check `/health` — `analysis_ready` should become `true` once the remote GPU is reachable and loaded.

## 3. SSH tunnel (no public IP)

If the GPU is reachable via SSH but not on a public IP:

```bash
# On CPU machine — forward local 8080 to GPU's 8080
ssh -N -L 8080:127.0.0.1:8080 user@gpu-server
```

CPU `.env`:

```env
CV_ANALYSIS_INFERENCE_MODE=remote
CV_ANALYSIS_LLAMA_SERVER_URL=http://127.0.0.1:8080
```

## 4. API

OpenAI-compatible endpoint (same as llama-server):

```bash
curl -X POST http://GPU_IP:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-key" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are an ATS analyst. Return JSON only."},
      {"role": "user", "content": "TASK: cv.analyze.standalone\nRESUME_TEXT:\n..."}
    ],
    "temperature": 0.1,
    "max_tokens": 800
  }'
```

## 5. Hosting options

| Platform | Notes |
|----------|-------|
| **RunPod / Lambda / Vast.ai** | Rent GPU, run `./scripts/run_gpu_inference.sh` |
| **Modal** | Wrap `gpu_inference.service:app` in a Modal web endpoint |
| **Colab + tunnel** | Dev only — ngrok/Cloudflare tunnel to port 8080 |
| **HF Inference Endpoints** | Upload merged model, use managed endpoint |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `analysis_ready: false` | GPU service not running or URL wrong |
| `status: loading` on `/health` | Wait for model download/load (~1–3 min) |
| `401 Unauthorized` | Match `CV_ANALYSIS_REMOTE_API_KEY` ↔ `GPU_INFERENCE_API_KEY` |
| CUDA OOM | Set `LOAD_IN_4BIT=true` (default) or use a 16 GB GPU |
| Slow first request | Model cold start — keep GPU service warm |
