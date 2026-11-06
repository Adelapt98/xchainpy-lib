# XChainPy: local development baseline

This is a **locally prepared, sanitized development snapshot** of the original MIT-licensed [XChainPy](https://github.com/xchainjs/xchainpy-lib). It is intended for extending the existing cross-chain Python interfaces with new clients such as Solana. It is **not audited or production-ready wallet software**.

## Current scope

| Package | Status |
| --- | --- |
| `xchainpy_util` | Asset/network operations covered by offline tests |
| `xchainpy_crypto` | BIP39 and keystore operations run on Python 3.12; tested locally |
| `xchainpy_client` | Shared client models/interfaces and HTTP adapter; mocked offline tests |
| `xchainpy_bitcoin` | Switched live read paths from dead SoChain v2 to Esplora; local SegWit signing verified; a **testnet3 read, broadcast and mined confirmation were evidenced on Windows** (see `TESTNET_VERIFICATION.md`); mainnet and production safety not verified |
| `xchainpy_litecoin` | Offline address and utility tests pass; live APIs unverified |
| `xchainpy_bitcoincash` | Offline address and fee tests pass; live APIs unverified |
| `xchainpy_ethereum` | Imports with `web3.py` 8 and has limited offline tests; live APIs unverified |
| `xchainpy_thorchain` | Legacy code retained as reference; old Cosmos/Binance SDK dependencies make it **unsupported** in this setup |

The obsolete `xchainpy_binance` module (BNB Beacon Chain) and its public chain symbols were deliberately removed. BNB Smart Chain is a different network and would require a separate implementation.

## Reproduce the environment

Requirements: Python 3.12 and [`uv`](https://docs.astral.sh/uv/).

```bash
bash scripts/setup_dev.sh
bash scripts/run_offline_tests.sh
BCL_DATA_DIR=.bitcoinlib-data .venv/bin/python scripts/check_imports.py
uv pip check --python .venv/bin/python
```

The seven tested packages are installed from **local editable paths**. The tests run without credentials or external RPC access. Old network integration tests that embedded historic mnemonic strings or used live endpoints were removed; deterministic fixtures and mocked transport tests replace them. **Do not use valuable wallet keys with this unaudited code.**

## Bitcoin testnet connectivity and broadcasts

Run this **read-only by default** testnet probe from a machine allowed to reach the Internet:

```bash
.venv/bin/python scripts/check_bitcoin_testnet.py
```

This checks the testnet chain tip, fee estimates, balance, UTXOs and transaction history using public addresses. If you have a *disposable, testnet-only* wallet with testnet coins and want to test real broadcast, set `XCHAINPY_TESTNET_MNEMONIC` securely in your local shell and explicitly opt in:

```bash
.venv/bin/python scripts/check_bitcoin_testnet.py --really-send-testnet --send-sats 2000
```

The script sends only on testnet to the same wallet's next derived address, never prints the phrase, and displays the public transaction ID. **Never use a mainnet or valuable recovery phrase.** The preparation environment could not reach external testnet hosts. On 6 November 2026, a user-run Windows session reported successful testnet3 read calls and broadcast acceptance, followed by an Explorer screenshot showing three mined confirmations. See `TESTNET_VERIFICATION.md` for the public transaction ID and verification boundary.

## Extending with a new chain

For a new chain client, use `xchainpy_client.base_xchain_client.BaseXChainClient` and the models in `xchainpy_client.models.types` as the shared interface. Add a separate package under `xchainpy/`, declare its optional dependencies, and include deterministic local tests before using network endpoints. Pay attention to derivation paths, transaction serialization, signer isolation, and network-specific asset units.

This baseline does **not** include a Solana implementation. Its requirements, code and tests are left for future development.

## Security and provenance

The source ZIP originally contained files called `mnemonic`, `infura` and `ether_api`, which could contain live recovery phrases and API credentials. They are not present in this baseline. Historic integration tests containing wallet recovery phrases were also removed. A **new sanitized Git history** was created for the delivered package. `.gitignore` protects these resource paths and generated files. The distributed ZIP excludes `.git/`, `.venv/`, `.uv-cache/`, `.bitcoinlib-data/` and caches.

Never commit or upload actual wallet secrets. Use disposable testnet wallets for any future integration work. No changes have been pushed to an external Git service.

## License

MIT. See [LICENSE](LICENSE) and the original project attribution.
