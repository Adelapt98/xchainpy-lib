# Bitcoin testnet verification status

**Prepared:** 5 November 2026. **Updated from user-run Windows output:** 6 November 2026. This document deliberately distinguishes offline verification, live RPC results, broadcast acceptance and mined confirmation.

## Confirmed locally

- Replaced Bitcoin's obsolete SoChain v2 read paths with documented Blockstream Esplora endpoints, for both mainnet and testnet: chain tip, address balance, UTXO lookup, transaction details/history and fee estimation.
- Corrected Bitcoin transaction input construction for native SegWit P2WPKH: the previous output's locking script and `public_hash` are now passed to `bitcoinlib` for signing.
- Successfully built, signed, serialized and locally verified a Bitcoin testnet-format transaction spending a **synthetic, nonexistent UTXO**. This proves local serialization/signing behavior, not consensus or mempool acceptance.
- Fixed derivation index mismatch between sender address and signing key, and added a local verification check that blocks broadcast on signature failure.
- Made unconfirmed UTXO spending opt-out by default, validated recipients before contacting network providers, and removed the obsolete Bitcoin SoChain/Haskoin adapter modules.
- Offline integration tests use deterministic fixtures and mocked HTTP.
- Test runner: **13 core + 9 UTXO utilities + 4 Ethereum asset + 66 offline regression = 92 passing**. All tests run without network access. Existing `bitcoinlib`/SQLAlchemy deprecation warnings remain.
- Local editable dependency check: seven packages install and import under Python 3.12; 75 installed distributions had no dependency conflicts.

## Live Windows testnet3 evidence supplied by the user

On **6 November 2026**, the user reported executing `scripts/check_bitcoin_testnet.py` successfully in Windows PowerShell, using the project's configured Blockstream Esplora testnet3 endpoint:

- Chain tip: `5301285` (read-only run) and `5301286` (broadcast run).
- Suggested fee: `263.193 sat/vB` (approximate provider estimate).
- Public source address: `tb1qvlm38w697hgt238v8655wq8mt9x40fv3fneel6`.
- Confirmed balance: `0.00194029 tBTC`; confirmed UTXOs: `1`; history: `1` transaction.
- Explicit opt-in: `--really-send-testnet --send-sats 2000`.
- Public destination address (same test wallet, index 1): `tb1quhn9tkr497huk4k3sx7hkcttkny7xhhslpuwf9`.
- Script output: `Broadcast accepted: 45292f4de014e4531fae9ffaf530d4568e967d2d21e609b0bb9f263e4c5cb7ba`.
- Explorer: <https://blockstream.info/testnet/tx/45292f4de014e4531fae9ffaf530d4568e967d2d21e609b0bb9f263e4c5cb7ba>.
- Subsequent **user-provided Blockstream Explorer screenshot** showed inclusion in testnet3 **block `5301287`** and **three confirmations** at screenshot time (initial copied text showed one confirmation).
- Explorer transaction: native SegWit, `222` bytes, `561` WU, `141` vB; input `194029` sat, output to wallet index 1 `2000` sat, change to source `154683` sat, and fee **`37346` sat** (`266.28 sat/vB` according to the explorer).

This is **user-supplied terminal and explorer screenshot evidence** of successful read-only operations, broadcaster acceptance and mined-block inclusion. The source wallet was disposable and the assets were testnet-only; no recovery phrase is stored in this report. The assistant could not independently retrieve the live explorer record from its restricted environment.

## Remaining verification limits

**The reported mined confirmation is supported by the user's Explorer screenshot**, but has not been independently retrieved by the assistant. The preparation environment's earlier attempt to access `https://blockstream.info/testnet/api/blocks/tip/height` was blocked by an external-network permission restriction before an HTTP response was received; a later attempt to retrieve the specific explorer entry was also inaccessible from the assistant environment. This does not contradict the user's successful Windows live run.

One successful testnet3 spend, even with mined confirmation, is **not a security audit** or proof that mainnet Bitcoin wallet operations are safe under adversarial or abnormal conditions. More test cases are needed for fee estimation, change handling, multiple UTXOs, errors and wallet recovery.

Likewise, Ethereum, Litecoin, Bitcoin Cash and the legacy THORChain adapter are **not** network-certified by this change. The THORChain adapter remains unsupported due to legacy dependencies; other chains have outdated or unverified network integrations.

## How to verify on a network-enabled machine

```bash
bash scripts/setup_dev.sh
bash scripts/run_offline_tests.sh
.venv/bin/python scripts/check_bitcoin_testnet.py
```

The last command performs read-only requests to public Bitcoin testnet endpoints. A successful run should print a block height, fee estimate, an address balance, UTXO count, and recent transaction count. Save the output (without secrets) to establish live RPC status.

If the read-only checks succeed, create a **new disposable testnet-only wallet** on your own computer, fund it with a small amount of *testnet* bitcoin and set `XCHAINPY_TESTNET_MNEMONIC` locally without exposing the phrase in chat, code, or screenshots. Then, and only with explicit intent to send:

```bash
.venv/bin/python scripts/check_bitcoin_testnet.py --really-send-testnet --send-sats 2000
```

This will send testnet coins to the disposable wallet's next derived address, print the public txid, and provide an explorer link. Confirm the returned txid appears on testnet and eventually receives block confirmation. **Never use any wallet holding real assets.**

## Provider references

- [Blockstream Esplora API documentation](https://github.com/Blockstream/esplora/blob/master/API.md)
- [SoChain API version errors](https://sochain.com/docs/errors), documenting that v2 endpoints are unavailable.

## Source and history

This output has a **new sanitized Git history**, separate from the original uploaded archive. No remote is configured, nothing was pushed, and the distributed source ZIP omits `.git`, environments and caches. An optional Git bundle is included separately for local restoration. Do **not** upload the Git bundle as task source code.
