# Deploy CV analysis model on Modal

Serve the fine-tuned ATS model on GPU in your Modal workspace (e.g. `bosyalaa224`).

## What gets deployed

- **App name:** `cv-analysis`
- **Endpoint:** `POST` JSON body:
  ```json
  {
    "resume_text": "...",
    "max_new_tokens": 800,
    "target_role": "Full Stack Developer"
  }
  ```
- **Response:** `{ "raw": "...", "parsed": { "overall_score": 75, ... } }`

This matches `analysis/model_client/modal_client.py` (`MODAL_ENDPOINT_URL`).

## 1. Upload your fine-tuned model to Hugging Face (if needed)

If training finished on Colab/Modal notebook and the weights are only local:

```bash
pip install huggingface_hub
huggingface-cli login

# Option A — upload adapter only (base + LoRA on Modal)
huggingface-cli upload bosyalaa224/cv-analysis-final-stage2 ./cv-analysis-final-stage2

# Option B — upload a fully merged model (single repo, faster load)
huggingface-cli upload bosyalaa224/cv-analysis-merged ./merged-model-folder
```

Use your repo names. The project defaults (Osama’s) are:

| Variable | Default |
|----------|---------|
| `ANALYSIS_BASE_MODEL_ID` | `OsamaHayba/qwen-ats-merged-stage1` |
| `ANALYSIS_ADAPTER_MODEL_ID` | `OsamaHayba/cv-analysis-final-stage2` |

Override these in the Modal secret if you use **your** HF repos.

## 2. Switch to your Modal account

```bash
cd ai-models
.venv/bin/pip3 install -r requirements-modal.txt
.venv/bin/modal setup
```

Dashboard: https://modal.com/apps/bosyalaa224/main

## 3. Create Modal secret (HF token + model IDs)

```bash
modal secret create cv-analysis-secrets \
  HF_TOKEN=hf_xxxxxxxx \
  ANALYSIS_BASE_MODEL_ID=OsamaHayba/qwen-ats-merged-stage1 \
  ANALYSIS_ADAPTER_MODEL_ID=bosyalaa224/cv-analysis-final-stage2
```

For a **single merged** model repo:

```bash
modal secret create cv-analysis-secrets \
  HF_TOKEN=hf_xxxxxxxx \
  ANALYSIS_MERGED_MODEL_ID=bosyalaa224/cv-analysis-merged
```

(`ANALYSIS_MERGED_MODEL_ID` skips base+adapter loading.)

## 4. Deploy

```bash
chmod +x scripts/deploy_modal_analysis.sh
./scripts/deploy_modal_analysis.sh
```

Or manually:

```bash
modal deploy analysis/infra/modal/server.py
```

Modal prints a URL like:

```text
https://bosyalaa224--cv-analysis-cvanalysismodel-analyze.modal.run
```

## 5. Wire local FastAPI

Edit `ai-models/.env`:

```env
MODAL_ENDPOINT_URL=https://bosyalaa224--cv-analysis-cvanalysismodel-analyze.modal.run
MODAL_REQUEST_TIMEOUT=300
```

Restart the API:

```bash
.venv/bin/python main.py
curl http://localhost:8000/health   # analysis_ready should be true
```

## 6. Test the endpoint directly

```bash
curl -X POST "$MODAL_ENDPOINT_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nFull Stack Developer\nSkills: Python, React, FastAPI\nExperience: Built APIs serving 2M users.",
    "target_role": "Full Stack Developer",
    "max_new_tokens": 800
  }'
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `401` / model download failed | Check `HF_TOKEN` in secret; model repo must be public or token has access |
| Cold start slow (1–3 min) | Normal on first request after idle; increase `scaledown_window` in `server.py` |
| `parsed` is null | Model returned non-JSON; check `raw` in response |
| Wrong workspace | `modal profile activate bosyalaa224` then redeploy |

## Files

| File | Role |
|------|------|
| `server.py` | Modal app + GPU loader + HTTP endpoint |
| `json_parse.py` | Parse model JSON output |
| `../../model_client/prompts.py` | Bundled into image (system + user prompt) |
