# XChainPY

### A modular Python SDK for multi-chain wallet and application development

XChainPY gives Python developers a shared foundation for interacting with different blockchains. It combines asset and network models, wallet cryptography, address derivation, provider adapters, balance and transaction queries, fee estimation, and transaction signing and broadcasting.

Applications can reuse common interfaces while choosing the chain-specific packages they need. The goal is to reduce duplicated integration work without hiding the differences between networks.

This repository continues the original [XChainJS community XChainPY project](https://github.com/xchainjs/xchainpy-lib), whose development was led by Adel Aboutalebi Pirnaeimi. The continuation is maintained under [Adelapt98](https://github.com/Adelapt98/xchainpy-lib), with earlier development history and subsequent modernization commits present in this checkout.

## What you can build

- Wallet interfaces that reuse asset, network and client models across chains.
- Address and transaction explorers backed by chain-specific providers.
- Testnet transaction workflows with local signing and explicit submission.
- New blockchain adapters that share the SDK's existing conventions.

The implementation is under active modernization. Use disposable testnet wallets for integration development. It has not received an independent security audit and is not presented as production-ready custody software.

## Packages and current support

| Package | Responsibility | Verification scope |
| --- | --- | --- |
| `xchainpy_util` | Asset, ticker and chain utilities | Offline tests |
| `xchainpy_crypto` | BIP39 helpers, derivation and encrypted keystores | Offline tests on Python 3.12 |
| `xchainpy_client` | Shared interfaces, models and HTTP support | Mocked offline contract tests |
| `xchainpy_bitcoin` | Bitcoin, Esplora reads and native SegWit transaction handling | Offline signing/provider tests and recorded testnet3 evidence |
| `xchainpy_litecoin` | Litecoin client and UTXO utilities | Offline utilities, live providers need validation |
| `xchainpy_bitcoincash` | Bitcoin Cash client and UTXO utilities | Offline utilities, live providers need validation |
| `xchainpy_ethereum` | Ethereum client and contract helpers | web3.py 8 compatibility with limited offline tests |
| `xchainpy_thorchain` | Historical THORChain client | Reference code, excluded from the supported installation |

The legacy Binance Beacon Chain module has been removed. BNB Smart Chain is a different integration and is not implemented by that removal. Solana is planned, not implemented.

## Recent development

- Updated the active development environment for Python 3.12.
- Replaced Bitcoin's obsolete SoChain read paths with Esplora.
- Improved native SegWit input construction, wallet-index handling and pre-broadcast signature checks.
- Updated Ethereum compatibility and removed obsolete SDK dependencies from the supported installation.
- Added deterministic regression tests for client contracts, provider responses and transaction handling.

See the [roadmap](ROADMAP.md) for the next reliability, integration and release milestones.

## Install from source

Use **Python 3.12** and run commands from the repository root. Install the local packages together so development changes are used instead of older PyPI releases.

### Linux and macOS

With [uv](https://docs.astral.sh/uv/) installed:

```bash
bash scripts/setup_dev.sh
bash scripts/run_offline_tests.sh
BCL_DATA_DIR=.bitcoinlib-data .venv/bin/python scripts/check_imports.py
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ./xchainpy/xchainpy_util -e ./xchainpy/xchainpy_crypto -e ./xchainpy/xchainpy_client -e ./xchainpy/xchainpy_bitcoin -e ./xchainpy/xchainpy_litecoin -e ./xchainpy/xchainpy_bitcoincash -e ./xchainpy/xchainpy_ethereum pytest pytest-asyncio
$env:BCL_DATA_DIR = (Join-Path (Get-Location) '.bitcoinlib-data')
./.venv/Scripts/python.exe scripts/check_imports.py
```

The [Windows testing guide](WINDOWS_TESTING_GUIDE.md) provides the offline test commands. The repository root is not a Python distribution, so root-level `pip install -e .` is not the installation workflow.

## Small offline example

```python
import os
os.environ.setdefault('BCL_DATA_DIR', '.bitcoinlib-data')

from xchainpy_util.asset import Asset
from xchainpy_client.models.types import Network
from xchainpy_bitcoin.client import Client
from xchainpy_bitcoin.models.client_types import BitcoinClientParams

asset = Asset.from_str('BTC.BTC')
client = Client(BitcoinClientParams(network=Network.Testnet))
assert asset.ticker == 'BTC'
assert client.get_network() == 'testnet'
print(asset)  # BTC.BTC
```

This example performs no RPC calls, loads no wallet phrase and broadcasts no transaction. Network queries and transfers are separate, explicit operations.

## Tests and integration evidence

The current offline suite passes **92 tests** across core utilities, cryptography, UTXO utilities, Ethereum asset handling and regression contracts. It uses deterministic fixtures and mocked providers rather than live wallet credentials.

[TESTNET_VERIFICATION.md](TESTNET_VERIFICATION.md) records the existing Bitcoin testnet3 evidence and its limits. Local signing checks, reported broadcast acceptance and reported mined confirmation are distinguished. Those results do not establish mainnet safety or certify other chain clients.

The testnet probe is read-only by default. Broadcasting requires an explicit opt-in and a disposable testnet-only wallet. Follow the linked guide rather than placing secrets in source files.

## Development direction

The next milestones strengthen existing clients, add useful chain integrations and improve release reproducibility. Priorities include Bitcoin amount and fee handling, consistent provider errors and pagination, Solana support, Ethereum transaction workflows, and automated cross-package checks.

New adapters should include explicit network configuration, documented asset units, deterministic serialization tests and a clear separation between local signing and network submission. Completion criteria are listed in [ROADMAP.md](ROADMAP.md).

## Repository layout

```text
xchainpy/
  xchainpy_util/          Assets and chains
  xchainpy_crypto/        Wallet cryptography and keystores
  xchainpy_client/        Shared interfaces and models
  xchainpy_bitcoin/       Bitcoin client and Esplora provider
  xchainpy_litecoin/      Litecoin client
  xchainpy_bitcoincash/   Bitcoin Cash client
  xchainpy_ethereum/      Ethereum client
  xchainpy_thorchain/     Historical reference code
scripts/                 Setup, import checks and testnet probe
tests_offline/           Isolated regression tests
```

## Credentials and shared examples

Keep RPC tokens, recovery phrases, private keys and wallet data outside the repository. Use invented records and documented public test vectors for shared examples. Never fund a wallet derived from a published test vector.

## License

Licensed under the [MIT license](LICENSE).
