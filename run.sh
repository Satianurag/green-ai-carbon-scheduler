#!/usr/bin/env bash
set -euo pipefail

# Pick preferred python binary (prefer 3.11 for widest wheel support)
for CAND in python3.11 python3.12 python3 python; do
  if command -v "$CAND" >/dev/null 2>&1; then
    PYBIN="$CAND"
    break
  fi
done
if [ -z "${PYBIN:-}" ]; then
  echo "No python interpreter found" >&2
  exit 1
fi

# Create or refresh virtual environment
if [ ! -d ".venv" ]; then
  set +e
  $PYBIN -m venv .venv
  VENV_STATUS=$?
  if [ $VENV_STATUS -ne 0 ]; then
    $PYBIN -m ensurepip --upgrade || true
    $PYBIN -m pip install --user --upgrade virtualenv || true
    $PYBIN -m virtualenv .venv
  fi
  set -e
fi

# If venv exists but pip is missing (created before python3-venv was installed), recreate
# If venv exists but pip is missing or wrong interpreter version, recreate
if [ ! -x ".venv/bin/pip" ]; then
  rm -rf .venv
  $PYBIN -m venv .venv
  .venv/bin/python -m ensurepip --upgrade || true
fi

# Ensure venv python matches chosen interpreter major.minor, else recreate
VENV_PY_VER=$(.venv/bin/python - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)
HOST_PY_VER=$($PYBIN - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)
if [ "$VENV_PY_VER" != "$HOST_PY_VER" ]; then
  rm -rf .venv
  $PYBIN -m venv .venv
  .venv/bin/python -m ensurepip --upgrade || true
fi

VENV_PY=".venv/bin/python"

# Install dependencies
$VENV_PY -m pip install --upgrade pip
$VENV_PY -m pip install -r requirements.txt

# Create artifacts dir if missing
mkdir -p artifacts

# Quick baseline and optimized runs (live UK CI, threshold=200 gCO2/kWh)
PYTHONPATH=src $VENV_PY -m greenai.cli run --mode baseline --ci live --threshold 200 --out artifacts/evidence.csv --log-decision artifacts/carbon_aware_decision.json
PYTHONPATH=src $VENV_PY -m greenai.cli run --mode optimized --ci live --threshold 200 --out artifacts/evidence.csv --log-decision artifacts/carbon_aware_decision.json

# Optional: small experiment (N=10) and plots
PYTHONPATH=src $VENV_PY -m greenai.cli experiment --runs 10 --ci live --out artifacts/evidence.csv --plots artifacts/
