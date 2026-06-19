#!/usr/bin/env bash
# One-time setup: Python venv + pip install requirements.txt
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PY=".venv/bin/python3"

_venv_python_runs() {
  [[ -x "$PY" ]] && "$PY" -c "import sys; sys.exit(0)" 2>/dev/null
}

_venv_is_real() {
  # True when python is an isolated venv, not a symlink to /usr/bin/python3
  _venv_python_runs && "$PY" -c "import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null
}

_venv_has_deps() {
  _venv_python_runs && "$PY" -c "import dotenv, fastapi" 2>/dev/null
}

_stale_activate() {
  [[ -f .venv/bin/activate ]] && grep -q 'cv_agent_repo' .venv/bin/activate 2>/dev/null
}

_fix_activate_path() {
  if [[ -f .venv/bin/activate ]]; then
    sed -i "s|cv_agent_repo/.venv|ai-models/.venv|g" .venv/bin/activate
    sed -i "s|^VIRTUAL_ENV=.*|VIRTUAL_ENV='${ROOT}/.venv'|" .venv/bin/activate
  fi
}

_create_venv() {
  echo "Creating .venv…"
  if command -v uv >/dev/null 2>&1; then
    echo "Using uv…"
    uv venv .venv --python python3
    return 0
  fi
  if python3 -m venv .venv 2>/dev/null && _venv_is_real; then
    return 0
  fi
  rm -rf .venv

  cat <<EOF >&2
❌ Could not create a Python virtual environment.

On Ubuntu/Debian, install the venv package for your Python version, then re-run:

  sudo apt update
  sudo apt install python3-venv python3.12-venv

Or install uv (https://docs.astral.sh/uv/) and re-run:

  curl -LsSf https://astral.sh/uv/install.sh | sh
  ./scripts/setup.sh

EOF
  exit 1
}

_bootstrap_pip() {
  if "$PY" -m pip --version &>/dev/null; then
    return 0
  fi
  echo "Bootstrapping pip…"
  if "$PY" -m ensurepip --upgrade 2>/dev/null; then
    return 0
  fi
  TMP="$(mktemp)"
  curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$TMP"
  "$PY" "$TMP"
  rm -f "$TMP"
}

# Working venv with deps → only fix stale activate paths, then exit
if _venv_has_deps; then
  if _stale_activate; then
    echo "Fixing outdated activate path (cv_agent_repo → ai-models)…"
    _fix_activate_path
  fi
  echo "✅ .venv already has dependencies — nothing to install."
  echo "Start: ./scripts/run.sh"
echo "HF login: .venv/bin/hf auth login"
  exit 0
fi

# Broken partial venv (failed apt create, or python → system /usr/bin)
if [[ -d .venv ]] && ! _venv_is_real; then
  echo "Removing incomplete .venv (not a real virtualenv)…"
  rm -rf .venv
fi

# Recreate if missing
if [[ ! -d .venv ]]; then
  _create_venv
fi

_fix_activate_path
_bootstrap_pip

echo "Installing Python dependencies (may take several minutes)…"
if command -v uv >/dev/null 2>&1; then
  uv pip install -r requirements.txt
else
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r requirements.txt
fi

if ! "$PY" -c "import multipart" 2>/dev/null; then
  "$PY" -m pip install python-multipart
fi

if ! _venv_has_deps; then
  echo "❌ Setup failed — could not import dotenv/fastapi in .venv"
  exit 1
fi

echo ""
echo "✅ Setup complete."
echo "CV analysis judge: ./scripts/install_llama_server.sh  (builds bin/llama-server)"
echo "GGUF model:        python scripts/download_gguf.py"
echo "Start: ./scripts/run.sh"
echo "HF login: .venv/bin/hf auth login"
echo "Stop:  ./scripts/stop.sh"
