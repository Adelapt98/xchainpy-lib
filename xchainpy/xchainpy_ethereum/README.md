# Ethereum client

Ethereum and contract helpers updated for web3.py 8, HTTP JSON-RPC and Etherscan v2 ABI requests.

## Current status

Limited offline compatibility tests. Live transaction workflows need broader verification.

## Development setup

Follow the [repository setup and tests](../../README.md), which install active packages from local editable paths on Python 3.12. The THORChain reference package is excluded from that workflow. Importing a client does not verify its live provider.

See the [roadmap](../../ROADMAP.md) and the [Bitcoin-specific verification record](../../TESTNET_VERIFICATION.md) for planned work and integration boundaries.

## Credentials

Keep RPC credentials, recovery phrases and private keys outside the source tree. Shared tests should use documented public fixtures and mocked providers. Never fund a wallet derived from a published test vector.

## License

MIT. The existing [package license and copyright notice](LICENSE) are retained.
