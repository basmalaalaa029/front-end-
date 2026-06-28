#!/usr/bin/env bash
# Validate a MongoDB Atlas connection string format.
# Usage: ./scripts/deploy/verify-atlas-uri.sh "mongodb+srv://..."
set -euo pipefail

URI="${1:-}"

if [[ -z "$URI" ]]; then
  echo "Usage: $0 <MONGODB_URI>"
  echo "Example: $0 'mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/careerpilot'"
  exit 1
fi

if [[ "$URI" == mongodb+srv://* ]]; then
  echo "OK: Atlas SRV URI format detected."
elif [[ "$URI" == mongodb://* ]]; then
  echo "WARN: Standard mongodb:// URI — Atlas typically uses mongodb+srv://"
else
  echo "ERROR: Invalid MongoDB URI (must start with mongodb:// or mongodb+srv://)"
  exit 1
fi

if [[ "$URI" == *"<password>"* || "$URI" == *"<user>"* ]]; then
  echo "ERROR: Replace <user> and <password> placeholders with real credentials."
  exit 1
fi

echo "URI length: ${#URI} chars — ready to set as MONGODB_URI on Render."
