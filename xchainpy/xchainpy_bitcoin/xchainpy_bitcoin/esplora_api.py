"""Bitcoin Esplora API adapter, shared by testnet and mainnet.

All amounts received from Esplora are integer satoshis. No private keys are
sent to the API. https://github.com/Blockstream/esplora/blob/master/API.md
"""

from datetime import datetime, timezone

import httpx
from bitcoinlib.keys import Address

from xchainpy_client.models.balance import Balance
from xchainpy_client.models.tx_types import TX, TxFrom, TxTo
from xchainpy_util.asset import AssetBTC

from .models.common import UTXO, Witness_UTXO


SATOSHIS_PER_BTC = 100_000_000


def api_base_url(blockstream_url, network):
    if network not in ('testnet', 'mainnet'):
        raise ValueError(f'Unsupported Bitcoin network: {network!r}')
    base = blockstream_url.rstrip('/')
    return f'{base}/testnet/api' if network == 'testnet' else f'{base}/api'


async def _get_json(url):
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def get_block_height(blockstream_url, network):
    """Read-only connectivity and chain-tip smoke check."""
    url = f'{api_base_url(blockstream_url, network)}/blocks/tip/height'
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return int(response.text.strip())


async def get_address_info(blockstream_url, network, address):
    return await _get_json(f'{api_base_url(blockstream_url, network)}/address/{address}')


async def get_balance(blockstream_url, network, address):
    data = await get_address_info(blockstream_url, network, address)
    sats = sum(
        data[f'{kind}_stats']['funded_txo_sum'] - data[f'{kind}_stats']['spent_txo_sum']
        for kind in ('chain', 'mempool')
    )
    return [Balance(asset=AssetBTC, amount=sats / SATOSHIS_PER_BTC)]


def _p2wpkh_locking_script(address, network):
    """XChainPy's Bitcoin wallet currently derives native SegWit P2WPKH keys."""
    parsed = Address.parse(address, network='bitcoin' if network == 'mainnet' else 'testnet')
    if parsed.script_type != 'p2wpkh' or len(parsed.hash_bytes) != 20:
        raise ValueError('Only native P2WPKH wallet addresses are supported for spends')
    return b'\x00\x14' + parsed.hash_bytes


async def get_unspent_txs(blockstream_url, network, address, confirmed_only=True):
    script = _p2wpkh_locking_script(address, network)
    data = await _get_json(f'{api_base_url(blockstream_url, network)}/address/{address}/utxo')
    return [
        UTXO(item['txid'], item['vout'], Witness_UTXO(item['value'], script))
        for item in data
        if not confirmed_only or item['status']['confirmed']
    ]


async def get_tx(blockstream_url, network, txid):
    return await _get_json(f'{api_base_url(blockstream_url, network)}/tx/{txid}')


async def get_transactions(blockstream_url, network, address, offset=0, limit=10):
    """Fetch sufficient recent Esplora pages for requested offset and limit."""
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be a non-negative integer')
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError('limit must be a positive integer')

    base = api_base_url(blockstream_url, network)
    info = await get_address_info(blockstream_url, network, address)
    total = info['chain_stats']['tx_count'] + info['mempool_stats']['tx_count']
    if offset >= total:
        return total, []

    txs = await _get_json(f'{base}/address/{address}/txs/mempool')
    last_confirmed_txid = None
    while len(txs) < min(total, offset + limit):
        suffix = f'/{last_confirmed_txid}' if last_confirmed_txid else ''
        confirmed = await _get_json(f'{base}/address/{address}/txs/chain{suffix}')
        if not confirmed:
            break
        txs.extend(confirmed)
        last_confirmed_txid = confirmed[-1]['txid']
    return total, txs[offset:offset + limit]


async def get_suggested_tx_fee(blockstream_url, network):
    estimates = await _get_json(f'{api_base_url(blockstream_url, network)}/fee-estimates')
    # Target confirmation within six blocks; never return a zero sat/vB fee.
    rate = estimates.get('6') or estimates.get('3') or estimates.get('1')
    if rate is None:
        raise ValueError('Esplora did not provide an expected fee estimate')
    return max(1.0, float(rate))


def parse_tx(tx):
    """Convert Esplora transaction JSON to XChainPy's shared TX model."""
    inputs = [
        TxFrom(previous['scriptpubkey_address'], previous['value'] / SATOSHIS_PER_BTC)
        for entry in tx['vin']
        if (previous := entry.get('prevout')) and previous.get('scriptpubkey_address')
    ]
    outputs = [
        TxTo(entry['scriptpubkey_address'], entry['value'] / SATOSHIS_PER_BTC)
        for entry in tx['vout']
        if entry.get('scriptpubkey_address')
    ]
    timestamp = tx.get('status', {}).get('block_time')
    date = datetime.fromtimestamp(timestamp, timezone.utc) if timestamp else datetime.now(timezone.utc)
    return TX(AssetBTC, inputs, outputs, date, 'transfer', tx['txid'])
