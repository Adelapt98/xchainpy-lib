# XChainPy testing guide for Windows PowerShell

This guide covers the maintained XChainPY checkout. Run all commands from the repository root in **PowerShell**, using an existing `.venv` when available. `bash scripts/*.sh` requires Bash and does not work in ordinary Windows PowerShell without Git Bash/WSL.

**Scope and safety:** Bitcoin **testnet3**, not testnet4, signet, or Bitcoin mainnet. Testnet coins have no monetary value. Do not use a real wallet or real funds. Never paste a seed phrase into websites, source code, screenshots, Git commits, or chat. The code is unaudited and is not safe for production funds.

## 1. Check your existing Python environment

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import pytest, xchainpy_bitcoin, xchainpy_crypto; print('Required imports OK')"
```

If you installed the environment using `uv`, you can additionally run `uv pip check --python .\.venv\Scripts\python.exe` when `uv` is available. Some `uv` environments do not include `pip` itself.

If `.venv` does not exist, create it with Python 3.12 and install the local packages before proceeding. Skip this setup if the environment already works:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\xchainpy\xchainpy_util -e .\xchainpy\xchainpy_crypto -e .\xchainpy\xchainpy_client -e .\xchainpy\xchainpy_bitcoin -e .\xchainpy\xchainpy_litecoin -e .\xchainpy\xchainpy_bitcoincash -e .\xchainpy\xchainpy_ethereum pytest pytest-asyncio
```

## 2. Run the offline regression tests

These tests use no wallet funds and make no Bitcoin network calls.

```powershell
$env:BCL_DATA_DIR = (Join-Path (Get-Location) '.bitcoinlib-data')
.\.venv\Scripts\python.exe -m pytest -q --import-mode=importlib .\xchainpy\xchainpy_crypto\tests .\xchainpy\xchainpy_util\tests
.\.venv\Scripts\python.exe -m pytest -q --import-mode=importlib .\xchainpy\xchainpy_bitcoin\tests\test_bitcoin_utils.py .\xchainpy\xchainpy_bitcoincash\tests\test_bitcoincash_utils.py .\xchainpy\xchainpy_litecoin\tests\test_litecoin_utils.py
.\.venv\Scripts\python.exe -m pytest -q --import-mode=importlib .\xchainpy\xchainpy_ethereum\tests\test_asset.py
.\.venv\Scripts\python.exe -m pytest -q --import-mode=importlib .\tests_offline
```

The preparation environment previously passed 92 offline tests. Your machine's result is authoritative for your installation.

## 3. Check the Bitcoin testnet3 API (read-only)

```powershell
.\.venv\Scripts\python.exe .\scripts\check_bitcoin_testnet.py
```

The script queries Blockstream Esplora for testnet3 block height, estimated fee rate, address balance, confirmed UTXOs and transaction history. By default it inspects a known public address, unless `XCHAINPY_TESTNET_MNEMONIC` is set in this PowerShell process. It does **not** broadcast a transaction without the `--really-send-testnet` flag.

## 4. Prepare a **disposable** testnet-only wallet

If you already created a test wallet and its address was printed by the script, **reuse the same seed**. Do not create a second wallet after funding the first. To check whether a mnemonic is currently loaded, without displaying it:

```powershell
if ($env:XCHAINPY_TESTNET_MNEMONIC) { 'Testnet wallet loaded' } else { 'No testnet wallet loaded' }
```

If this reports no wallet, reload the **same** disposable seed into this session (or generate a new test wallet **before** requesting any faucet coins). To reload without placing words literally in PowerShell command history:

```powershell
$env:XCHAINPY_TESTNET_MNEMONIC = Read-Host 'Enter disposable TESTNET-ONLY recovery phrase'
```

Only if you have *not* funded a prior address and need a fresh test-only wallet, generate a new mnemonic locally:

```powershell
.\.venv\Scripts\python.exe -c "from xchainpy_crypto import crypto; print(crypto.generate_mnemonic())"
```

Record the new test-only phrase securely, then load it via `Read-Host` above. The generation command prints the phrase to your own terminal, so avoid recording or sharing that screen. The variable is temporary and disappears when this PowerShell session ends; keep the test phrase until all testnet coins have been sent/spent.

Run the read-only check again:

```powershell
.\.venv\Scripts\python.exe .\scripts\check_bitcoin_testnet.py
```

Copy the `Checking address: tb1...` value. **Verify that the address remains identical on every run** before funding or broadcasting.

## 5. Obtain free testnet3 Bitcoin (tBTC)

The XChainPy repository **does not automatically obtain, mine, or credit testnet coins**. This requires a separate faucet or a testnet funding wallet. A faucet request is external and subject to availability, limits, or CAPTCHA.

1. Open the specifically labelled **testnet3** faucet at <https://coinfaucet.eu/en/btc-testnet/>.
2. Paste only your **public** `tb1...` testnet3 address in its address field.
3. Request testnet coins. **Never** enter the recovery phrase or private key into a faucet.
4. If a faucet fails, look for another provider explicitly supporting **testnet3**. Some similarly named Bitcoin faucets now fund **testnet4** and will not fund the chain this repository currently queries.
5. Wait until the funding transaction has been confirmed. Then rerun the read-only command above until it reports `Confirmed UTXOs: 1` or more, with nonzero balance.

**High fee warning:** One observed provider fee estimate was `264.132 sat/vB`. The transaction builder estimates the total fee from its input/output count and this rate, so an amount as small as 2,000 sat may require roughly **40,000+ sat total** to broadcast with one input. More inputs increase the fee. About `0.0005 tBTC` (50,000 sat) might be enough for one simple test at that snapshot rate, but is **not guaranteed**. Prefer a larger confirmed balance or wait until fees drop. Do not run the broadcast command until the script shows sufficient confirmed funds.

## 6. Broadcast one real **testnet-only** transaction (explicit opt-in)

**This step is not read-only.** It spends disposable testnet coins and broadcasts on testnet3. The code signs locally and sends to a second address derived from the *same* test-only mnemonic (index 1). It is still a development verification, not a production wallet certification.

First verify `Checking address` matches the funded address and you have confirmed UTXOs. Then, only when you intend to broadcast:

```powershell
.\.venv\Scripts\python.exe .\scripts\check_bitcoin_testnet.py --really-send-testnet --send-sats 2000
```

Expected on success: `Broadcast accepted: <txid>` and an explorer URL. Open the URL on the **testnet** explorer, confirm the transaction appears, and later verify at least one block confirmation. If a broadcaster rejects the transaction, save only the public error/txid and do not expose your mnemonic.

To check the public transaction's confirmation status and actual fee directly from the testnet3 API, replace the placeholder with your **public** txid:

```powershell
$txid = 'PASTE_PUBLIC_TXID_HERE'
$tx = Invoke-RestMethod -Uri "https://blockstream.info/testnet/api/tx/$txid"
$tx.status | Format-List
"Fee paid: $($tx.fee) sat"
```

`confirmed: False` means the transaction is not yet included in a block. Retry later. `confirmed: True` together with `block_height` is evidence of a mined confirmation on testnet3.

You can inspect the destination address with the public txid in the explorer. This script's default balance check examines wallet index **0**, while the receiving address is index **1**; do not expect the index-1 deposit to appear in the index-0 balance.

## 7. What is and is not proven

| Check | Evidence |
| --- | --- |
| Offline unit tests | Python logic and mocked network contracts, without network access |
| Read-only testnet3 script | Live connectivity, address data and fee/UTXO queries |
| Successful `--really-send-testnet` response | Signed transaction accepted for broadcast by the provider |
| Transaction confirmed in a block | On-chain inclusion on testnet3 |

Even all four checks together do **not** establish that mainnet Bitcoin signing is production-safe, or that the other blockchain packages function over their live networks. Security review, failure-case testing and independent transaction verification would still be needed.

## References

- [Blockstream Esplora API](https://github.com/Blockstream/esplora/blob/master/API.md)
- [Bitcoin testnet3 faucet](https://coinfaucet.eu/en/btc-testnet/)
- [Bitcoin testnet verification status](TESTNET_VERIFICATION.md)
