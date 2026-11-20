"""Transport contract tests against documented Esplora JSON responses.

All HTTP responses are simulated; these tests never contact a live server.
"""

import pytest

from xchainpy_bitcoin import blockstream_api, esplora_api, utils
from xchainpy_bitcoin.crypto import mnemonic_to_address, mnemonic_to_private_key
from xchainpy_bitcoin.models.common import UTXO, Witness_UTXO


# Public BIP39 vectors: https://github.com/trezor/python-mnemonic/blob/master/vectors.json
TEST_PHRASE = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
TEST_PATH = "m/84'/1'/0'/0/0"
TEST_ADDRESS = mnemonic_to_address(TEST_PHRASE, TEST_PATH, 'testnet')


class MockResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status_code = status
        self.text = body if isinstance(body, str) else ''

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')

    def json(self):
        return self.body


def mock_http(monkeypatch, responses):
    calls = []

    class FakeClient:
        def __init__(self, timeout):
            assert timeout == 15

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            calls.append(('GET', url))
            if url not in responses:
                raise AssertionError(f'Unexpected GET {url}')
            return MockResponse(responses[url])

        async def post(self, url, content, headers):
            calls.append(('POST', url, content, headers))
            return MockResponse('abc123')

    monkeypatch.setattr(esplora_api.httpx, 'AsyncClient', FakeClient)
    return calls


@pytest.mark.parametrize('network,expected', [
    ('testnet', 'https://blockstream.info/testnet/api'),
    ('mainnet', 'https://blockstream.info/api'),
])
def test_esplora_endpoint_selection(network, expected):
    assert esplora_api.api_base_url('https://blockstream.info/', network) == expected


def test_esplora_invalid_network_rejected():
    with pytest.raises(ValueError):
        esplora_api.api_base_url('https://blockstream.info', 'signet')


@pytest.mark.asyncio
async def test_live_chain_tip_endpoint_contract_without_network(monkeypatch):
    url = 'https://blockstream.info/testnet/api/blocks/tip/height'
    calls = mock_http(monkeypatch, {url: '424242'})
    assert await esplora_api.get_block_height('https://blockstream.info', 'testnet') == 424242
    assert calls == [('GET', url)]


@pytest.mark.asyncio
async def test_balance_combines_confirmed_and_mempool_values(monkeypatch):
    url = f'https://blockstream.info/testnet/api/address/{TEST_ADDRESS}'
    mock_http(monkeypatch, {url: {
        'chain_stats': {'tx_count': 2, 'funded_txo_sum': 310000, 'spent_txo_sum': 100000},
        'mempool_stats': {'tx_count': 1, 'funded_txo_sum': 20000, 'spent_txo_sum': 5000},
    }})
    [balance] = await esplora_api.get_balance('https://blockstream.info', 'testnet', TEST_ADDRESS)
    assert balance.amount == 0.00225


@pytest.mark.asyncio
async def test_utxo_conversion_filters_unconfirmed_and_builds_script(monkeypatch):
    url = f'https://blockstream.info/testnet/api/address/{TEST_ADDRESS}/utxo'
    responses = [{
        'txid': '11' * 32, 'vout': 1, 'value': 123456,
        'status': {'confirmed': True},
    }, {
        'txid': '22' * 32, 'vout': 2, 'value': 3000,
        'status': {'confirmed': False},
    }]
    mock_http(monkeypatch, {url: responses})
    confirmed = await esplora_api.get_unspent_txs('https://blockstream.info', 'testnet', TEST_ADDRESS)
    assert len(confirmed) == 1
    assert confirmed[0].hash == '11' * 32
    assert confirmed[0].index == 1
    assert confirmed[0].witness_utxo.value == 123456
    assert bytes(confirmed[0].witness_utxo.script).startswith(b'\x00\x14')
    all_utxos = await esplora_api.get_unspent_txs('https://blockstream.info', 'testnet', TEST_ADDRESS, False)
    assert len(all_utxos) == 2


@pytest.mark.asyncio
async def test_transaction_history_uses_esplora_pagination(monkeypatch):
    base = 'https://blockstream.info/testnet/api'
    info = {'chain_stats': {'tx_count': 27}, 'mempool_stats': {'tx_count': 1}}
    first = [{'txid': f'{idx:064x}'} for idx in range(1, 26)]
    second = [{'txid': f'{idx:064x}'} for idx in range(26, 28)]
    calls = mock_http(monkeypatch, {
        f'{base}/address/{TEST_ADDRESS}': info,
        f'{base}/address/{TEST_ADDRESS}/txs/mempool': [{'txid': 'ff' * 32}],
        f'{base}/address/{TEST_ADDRESS}/txs/chain': first,
        f'{base}/address/{TEST_ADDRESS}/txs/chain/{first[-1]["txid"]}': second,
    })
    total, page = await esplora_api.get_transactions(
        'https://blockstream.info', 'testnet', TEST_ADDRESS, offset=25, limit=2)
    assert total == 28
    assert page == [first[-1], second[0]]
    assert len(calls) == 4


@pytest.mark.asyncio
async def test_fee_estimates_and_broadcast_contract(monkeypatch):
    base = 'https://blockstream.info/testnet/api'
    calls = mock_http(monkeypatch, {f'{base}/fee-estimates': {'1': 4.0, '6': 2.5}})
    assert await esplora_api.get_suggested_tx_fee('https://blockstream.info', 'testnet') == 2.5
    assert await blockstream_api.broadcast_tx('https://blockstream.info', 'testnet', '0102') == 'abc123'
    assert calls[-1] == ('POST', f'{base}/tx', '0102', {'Content-Type': 'text/plain'})


@pytest.mark.asyncio
async def test_broadcast_refuses_malformed_hex_before_http(monkeypatch):
    calls = mock_http(monkeypatch, {})
    with pytest.raises(ValueError, match='hexadecimal'):
        await blockstream_api.broadcast_tx('https://blockstream.info', 'testnet', 'zz')
    assert not calls


def test_esplora_transaction_mapping():
    mapped = esplora_api.parse_tx({
        'txid': 'aa' * 32,
        'status': {'confirmed': True, 'block_time': 1_600_000_000},
        'vin': [{'prevout': {'scriptpubkey_address': TEST_ADDRESS, 'value': 20000}}],
        'vout': [{'scriptpubkey_address': TEST_ADDRESS, 'value': 19000}],
    })
    assert mapped.tx_hash == 'aa' * 32
    assert mapped.tx_from[0].amount == 0.0002
    assert mapped.tx_to[0].amount == 0.00019


@pytest.mark.asyncio
async def test_build_and_sign_native_segwit_transaction_offline(monkeypatch):
    """Tests actual bitcoinlib signing against a synthetic, unfunded UTXO."""
    script = esplora_api._p2wpkh_locking_script(TEST_ADDRESS, 'testnet')
    fake_utxo = UTXO('11' * 32, 0, Witness_UTXO(100000, script))

    async def fake_scan(*args, **kwargs):
        return [fake_utxo]

    async def fake_balance(*args, **kwargs):
        return [type('BalanceStub', (), {'amount': 0.001})()]

    monkeypatch.setattr(utils, 'scan_UTXOs', fake_scan)
    monkeypatch.setattr(utils, 'get_balance', fake_balance)
    tx, utxos = await utils.build_tx(
        sochain_url='https://blockstream.info', amount=50000,
        recipient=TEST_ADDRESS, memo='', fee_rate=2,
        sender=TEST_ADDRESS, network='testnet')
    assert utxos == [fake_utxo]
    tx.sign(mnemonic_to_private_key(TEST_PHRASE, TEST_PATH, 'testnet').Raw().ToBytes())
    assert tx.verify()
    assert tx.raw_hex().startswith('01000000')
