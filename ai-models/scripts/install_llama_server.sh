#!/usr/bin/env bash
# Install llama-server for cv_analysis — prebuilt binary + shared libs (no cmake).
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
INSTALL_DIR="${ROOT}/vendor/llama-server"
BIN="${INSTALL_DIR}/llama-server"

if [[ -x "$BIN" ]]; then
  echo "✅ llama-server already installed: $BIN"
  LD_LIBRARY_PATH="${INSTALL_DIR}" "$BIN" --version 2>/dev/null || true
  exit 0
fi

TAG="${LLAMA_CPP_TAG:-b9716}"
ASSET="llama-${TAG}-bin-ubuntu-x64.tar.gz"
URL="https://github.com/ggml-org/llama.cpp/releases/download/${TAG}/${ASSET}"
TMP="${ROOT}/vendor/llama-prebuilt"

echo "Downloading prebuilt llama-server (${TAG}, Ubuntu x64 CPU)…"
rm -rf "$TMP" "$INSTALL_DIR"
mkdir -p "$TMP"
curl -fsSL "$URL" -o "${TMP}/${ASSET}"
tar -xzf "${TMP}/${ASSET}" -C "$TMP"

EXTRACTED="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
SERVER_SRC="$(find "$TMP" -type f -name 'llama-server' | head -1)"
if [[ -z "$SERVER_SRC" || ! -f "$SERVER_SRC" ]]; then
  echo "❌ llama-server not found in ${ASSET}"
  exit 1
fi
EXTRACTED="$(dirname "$SERVER_SRC")"

mkdir -p "$INSTALL_DIR"
cp -a "${EXTRACTED}/." "$INSTALL_DIR/"
chmod +x "${INSTALL_DIR}/llama-server"

# Wrapper so subprocess can invoke without manual LD_LIBRARY_PATH
cat > "${ROOT}/bin/llama-server" <<EOF
#!/usr/bin/env bash
export LD_LIBRARY_PATH="${INSTALL_DIR}:\${LD_LIBRARY_PATH:-}"
exec "${INSTALL_DIR}/llama-server" "\$@"
EOF
chmod +x "${ROOT}/bin/llama-server"

echo "✅ Installed llama-server:"
echo "   ${ROOT}/bin/llama-server  (wrapper)"
echo "   ${INSTALL_DIR}/            (libs + binary)"
LD_LIBRARY_PATH="${INSTALL_DIR}" "${INSTALL_DIR}/llama-server" --version 2>/dev/null || true
