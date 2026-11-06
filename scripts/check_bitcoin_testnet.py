#!/usr/bin/env python3
"""Opt-in Bitcoin testnet live smoke test; safe, read-only by default.

This script deliberately never accepts a mnemonic on the command line, never
prints private material, and will not broadcast unless explicitly requested.
Only use disposable *testnet* wallets; never supply a real-money seed phrase.
"""

import argparse
import asyncio
import os

from xchainpy_bitcoin import esplora_api
from xchainpy_bitcoin.client import Client
from xchainpy_bitcoin.models.client_types import BitcoinClientParams, BitcoinTxParams


PUBLIC_TEST_ADDRESS = 'tb1qtpzjcs48dtzz40hdcm5sljm3cqduwq2v6tss9p'
BLOCKSTREAM = 'https://blockstream.info'


async def run_live(args):
    print('Bitcoin testnet Esplora read-only checks')
    height = await esplora_api.get_block_height(BLOCKSTREAM, 'testnet')
    print(f'Chain tip: {height}')
    fee_rate = await esplora_api.get_suggested_tx_fee(BLOCKSTREAM, 'testnet')
    print(f'Estimated fee (sat/vB): {fee_rate}')

    phrase = os.environ.get('XCHAINPY_TESTNET_MNEMONIC')
    if args.really_send_testnet and not phrase:
        raise SystemExit('Set XCHAINPY_TESTNET_MNEMONIC with a disposable testnet-only seed.')
    client = Client(BitcoinClientParams(network='testnet', phrase=phrase)) if phrase else None
    address = client.get_address() if client else args.address
    print(f'Checking address: {address}')
    [balance] = await esplora_api.get_balance(BLOCKSTREAM, 'testnet', address)
    print(f'Balance: {balance.amount} tBTC')
    utxos = await esplora_api.get_unspent_txs(BLOCKSTREAM, 'testnet', address)
    print(f'Confirmed UTXOs: {len(utxos)}')
    total, transactions = await esplora_api.get_transactions(BLOCKSTREAM, 'testnet', address, limit=5)
    print(f'Transactions: {total} total, {len(transactions)} returned')

    if not args.really_send_testnet:
        print('Read-only checks complete. Nothing was broadcast.')
        return

    if args.send_sats <= 1000:
        raise SystemExit('Set --send-sats above 1000 (Bitcoin dust threshold).')
    if balance.amount * 100_000_000 < args.send_sats + 5000:
        raise SystemExit('Insufficient testnet coins for the amount and approximate network fee.')

    # Sending to index 1 is intentionally a different address from index 0.
    destination = client.get_address(1)
    print(f'Broadcasting {args.send_sats} testnet satoshis to {destination}')
    txid = await client.transfer(BitcoinTxParams(
        amount=args.send_sats / 100_000_000,
        recipient=destination,
        fee_rate=max(1, round(fee_rate)),
    ))
    print(f'Broadcast accepted: {txid}')
    print(f'Explorer: {client.get_explorer_tx_url(txid)}')
    print('Use the explorer to confirm inclusion in a mined block.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', default=PUBLIC_TEST_ADDRESS,
                        help='Public Bitcoin testnet address for read-only inspection.')
    parser.add_argument('--really-send-testnet', action='store_true',
                        help='Explicitly broadcast a transaction from a testnet-only wallet.')
    parser.add_argument('--send-sats', type=int, default=2000,
                        help='Amount to send on testnet if broadcasting is opted in.')
    args = parser.parse_args()
    asyncio.run(run_live(args))


if __name__ == '__main__':
    main()
