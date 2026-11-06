#!/usr/bin/env bash
# Reproducible local setup; only active, supported baseline packages are installed.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo 'uv is required (https://docs.astral.sh/uv/getting-started/installation/).' >&2
  exit 1
fi

uv venv .venv --python 3.12
uv pip install --python .venv/bin/python \
  -e xchainpy/xchainpy_util \
  -e xchainpy/xchainpy_crypto \
  -e xchainpy/xchainpy_client \
  -e xchainpy/xchainpy_bitcoin \
  -e xchainpy/xchainpy_litecoin \
  -e xchainpy/xchainpy_bitcoincash \
  -e xchainpy/xchainpy_ethereum \
  pytest pytest-asyncio

echo 'Installed local packages. Run: bash scripts/run_offline_tests.sh'
