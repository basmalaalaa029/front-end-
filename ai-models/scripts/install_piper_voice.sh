#!/usr/bin/env bash
# Install Piper voice for interview TTS (/speak) — zip default voice.
# No sudo required. Also needs espeak-ng for phonemization.
set -euo pipefail

VOICE_DIR="${PIPER_VOICE_DIR:-$HOME/piper-voices}"
VOICE_NAME="en_US-lessac-medium"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"

mkdir -p "$VOICE_DIR"

for ext in onnx "onnx.json"; do
  dest="$VOICE_DIR/${VOICE_NAME}.${ext}"
  if [[ -f "$dest" ]]; then
    echo "==> Already exists: $dest"
    continue
  fi
  echo "==> Downloading ${VOICE_NAME}.${ext}"
  curl -fsSL -L "${BASE}/${VOICE_NAME}.${ext}" -o "$dest"
done

echo ""
echo "Piper voice installed to: $VOICE_DIR/${VOICE_NAME}.onnx"
echo ""
echo "Optional — espeak-ng (phonemes, may need sudo on some systems):"
echo "  sudo apt install espeak-ng"
echo ""
echo "Add to ai-models/.env (optional):"
echo "  PIPER_MODEL_PATH=$VOICE_DIR/${VOICE_NAME}.onnx"
echo ""
echo "Restart the backend, then test:"
echo "  curl -X POST http://localhost:8000/speak -F 'text=Hello' -o /tmp/test.wav"
