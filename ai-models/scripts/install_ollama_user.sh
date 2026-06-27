#!/usr/bin/env bash
# Install Ollama without sudo (no snap, no admin).
# Usage:
#   ./scripts/install_ollama_user.sh          # user-local binary (default)
#   ./scripts/install_ollama_user.sh docker   # via Docker (if docker works)
set -euo pipefail

OLLAMA_VERSION="${OLLAMA_VERSION:-v0.30.11}"
INSTALL_DIR="${OLLAMA_INSTALL_DIR:-$HOME/.local/ollama}"
BIN_DIR="$INSTALL_DIR/bin"
METHOD="${1:-local}"

install_local() {
  echo "==> Installing Ollama ${OLLAMA_VERSION} to ${INSTALL_DIR} (no sudo)"

  if ! command -v curl >/dev/null; then
    echo "Error: curl is required." >&2
    exit 1
  fi
  if ! command -v unzstd >/dev/null && ! command -v zstd >/dev/null; then
    echo "Error: install zstd (sudo apt install zstd) or use: $0 docker" >&2
    exit 1
  fi

  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64)  ASSET="ollama-linux-amd64.tar.zst" ;;
    aarch64|arm64) ASSET="ollama-linux-arm64.tar.zst" ;;
    *)
      echo "Unsupported architecture: $ARCH" >&2
      exit 1
      ;;
  esac

  URL="https://github.com/ollama/ollama/releases/download/${OLLAMA_VERSION}/${ASSET}"
  TMP="$(mktemp /tmp/ollama-XXXXXX.tar.zst)"

  echo "==> Downloading ${URL}"
  curl -fsSL -L "$URL" -o "$TMP"

  mkdir -p "$INSTALL_DIR"
  echo "==> Extracting to ${INSTALL_DIR}"
  if command -v unzstd >/dev/null; then
    tar --use-compress-program=unzstd -xf "$TMP" -C "$INSTALL_DIR"
  else
    tar --use-compress-program=zstd -xf "$TMP" -C "$INSTALL_DIR"
  fi
  rm -f "$TMP"

  if [[ ! -x "$BIN_DIR/ollama" ]]; then
    echo "Error: expected binary at $BIN_DIR/ollama" >&2
    exit 1
  fi

  MARKER="# ollama user-local install"
  if ! grep -qF "$MARKER" "$HOME/.bashrc" 2>/dev/null; then
    cat >>"$HOME/.bashrc" <<EOF

$MARKER
export PATH="$BIN_DIR:\$PATH"
export LD_LIBRARY_PATH="$INSTALL_DIR/lib/ollama:\${LD_LIBRARY_PATH:-}"
EOF
    echo "==> Added PATH to ~/.bashrc"
  fi

  export PATH="$BIN_DIR:$PATH"
  export LD_LIBRARY_PATH="$INSTALL_DIR/lib/ollama:${LD_LIBRARY_PATH:-}"

  echo ""
  echo "Installed: $($BIN_DIR/ollama --version 2>/dev/null || echo ok)"
  echo ""
  echo "Next steps (run in separate terminals):"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
  echo "  export LD_LIBRARY_PATH=\"$INSTALL_DIR/lib/ollama:\${LD_LIBRARY_PATH:-}\""
  echo "  ollama serve"
  echo "  ollama pull nomic-embed-text"
}

install_docker() {
  echo "==> Starting Ollama via Docker (no sudo for snap)"

  if ! command -v docker >/dev/null; then
    echo "Error: docker not found." >&2
    exit 1
  fi

  if docker ps -a --format '{{.Names}}' | grep -qx ollama; then
    echo "Container 'ollama' already exists — starting it"
    docker start ollama >/dev/null 2>&1 || true
  else
    docker run -d \
      --name ollama \
      -v ollama:/root/.ollama \
      -p 11434:11434 \
      --restart unless-stopped \
      ollama/ollama
  fi

  echo "==> Waiting for API on http://localhost:11434 ..."
  for _ in $(seq 1 30); do
    if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  echo "==> Pulling nomic-embed-text"
  docker exec ollama ollama pull nomic-embed-text

  echo ""
  echo "Ollama is running at http://localhost:11434"
  echo "Your ai-models/.env should have:"
  echo "  OLLAMA_BASE_URL=http://localhost:11434"
  echo "  EMBEDDING_MODEL=nomic-embed-text"
}

case "$METHOD" in
  local|user|"") install_local ;;
  docker)        install_docker ;;
  *)
    echo "Usage: $0 [local|docker]" >&2
    exit 1
    ;;
esac
