#!/usr/bin/env bash
# Download static ffmpeg+ffprobe into ai-models/vendor/ffmpeg-static (no sudo).
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="vendor/ffmpeg-static"
URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

if [[ -x "$DEST/ffmpeg" && -x "$DEST/ffprobe" ]]; then
  echo "ffmpeg already installed at $DEST"
  "$DEST/ffprobe" -version | head -1
  exit 0
fi

echo "Downloading ffmpeg static build (~80MB)…"
mkdir -p vendor
curl -fsSL -o /tmp/ffmpeg-static.tar.xz "$URL"
tar xf /tmp/ffmpeg-static.tar.xz -C vendor
DIR=$(ls -d vendor/ffmpeg-*-amd64-static | head -1)
rm -rf "$DEST"
mv "$DIR" "$DEST"
rm -f /tmp/ffmpeg-static.tar.xz
echo "Installed:"
"$DEST/ffmpeg" -version | head -1
"$DEST/ffprobe" -version | head -1
