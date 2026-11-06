#!/usr/bin/env bash
# Safe offline-only checks. No RPC requests, wallet funding or transaction broadcast.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

export BCL_DATA_DIR="$PROJECT_DIR/.bitcoinlib-data"
export PYTHONPATH="$PROJECT_DIR/xchainpy/xchainpy_util:$PROJECT_DIR/xchainpy/xchainpy_crypto:$PROJECT_DIR/xchainpy/xchainpy_client:$PROJECT_DIR/xchainpy/xchainpy_bitcoin:$PROJECT_DIR/xchainpy/xchainpy_bitcoincash:$PROJECT_DIR/xchainpy/xchainpy_litecoin:$PROJECT_DIR/xchainpy/xchainpy_ethereum"

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo 'Create the local virtual environment first: bash scripts/setup_dev.sh' >&2
  exit 1
fi

"$PYTHON_BIN" -m pytest -q --import-mode=importlib xchainpy/xchainpy_crypto/tests xchainpy/xchainpy_util/tests
"$PYTHON_BIN" -m pytest -q --import-mode=importlib \
  xchainpy/xchainpy_bitcoin/tests/test_bitcoin_utils.py \
  xchainpy/xchainpy_bitcoincash/tests/test_bitcoincash_utils.py \
  xchainpy/xchainpy_litecoin/tests/test_litecoin_utils.py
"$PYTHON_BIN" -m pytest -q --import-mode=importlib xchainpy/xchainpy_ethereum/tests/test_asset.py
"$PYTHON_BIN" -m pytest -q --import-mode=importlib tests_offline
