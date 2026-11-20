"""Bitcoin adapter tests using mocks only, never a live wallet or RPC."""

from types import SimpleNamespace

import pytest

from xchainpy_bitcoin.client import Client
from xchainpy_bitcoin.models.client_types import BitcoinClientParams, BitcoinTxParams
from xchainpy_bitcoin import utils as bitcoin_utils
from xchainpy_client.models.tx_types import TxHistoryParams


# Public BIP39 vectors: https://github.com/trezor/python-mnemonic/blob/master/vectors.json
TEST_PHRASE = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'


def new_client(network='testnet'):
    return Client(BitcoinClientParams(network=network, phrase=TEST_PHRASE))


@pytest.mark.asyncio
async def test_transfer_uses_wallet_key_and_broadcast_adapter_only(monkeypatch):
    client = new_client()
    calls = []

    class FakeTransaction:
        def sign(self, private_key):
            assert isinstance(private_key, bytes)
            assert len(private_key) == 32
            calls.append('signed')

        def raw_hex(self):
            return '00aa'

        def verify(self):
            return True

    async def fake_build_tx(**kwargs):
        calls.append(('build', kwargs))
        return FakeTransaction(), []

    async def fake_broadcast_tx(url, network, raw_hex):
        calls.append(('broadcast', url, network, raw_hex))
        return 'fake-txid'

    monkeypatch.setattr(bitcoin_utils, 'build_tx', fake_build_tx)
    monkeypatch.setattr(bitcoin_utils, 'broadcast_tx', fake_broadcast_tx)
    params = BitcoinTxParams(amount=0.001, recipient=client.get_address(1), fee_rate=5)
    assert await client.transfer(params) == 'fake-txid'
    assert calls[0][0] == 'build'
    assert calls[0][1]['network'] == 'testnet'
    assert calls[0][1]['amount'] == 100_000
    assert calls[0][1]['sender'] == client.get_address()
    assert calls[1] == 'signed'
    assert calls[2] == ('broadcast', 'https://blockstream.info', 'testnet', '00aa')


@pytest.mark.asyncio
async def test_client_reads_balances_without_real_rpc(monkeypatch):
    client = new_client('mainnet')
    expected = [SimpleNamespace(amount=1.25)]

    async def fake_get_balance(url, address, network):
        assert network == 'mainnet'
        assert address == 'test-address'
        return expected

    monkeypatch.setattr(bitcoin_utils, 'get_balance', fake_get_balance)
    assert await client.get_balance('test-address') is expected


@pytest.mark.asyncio
async def test_bitcoin_uses_suggested_fees_if_thornode_unavailable(monkeypatch):
    client = new_client()

    async def failing_thornode():
        raise ConnectionError('offline')

    async def fallback_fee():
        return 12

    monkeypatch.setattr(client, 'get_fee_rate_from_thorchain', failing_thornode)
    monkeypatch.setattr(client, '_get_suggested_fee_rate', fallback_fee)
    fees = await client.get_fee_rates()
    assert (fees.fastest, fees.fast, fees.average) == (60, 12, 6)


@pytest.mark.asyncio
async def test_transaction_history_pagination_without_rpc(monkeypatch):
    from xchainpy_bitcoin import esplora_api

    client = new_client()
    fetched_ids = []

    async def fake_get_transactions(*args, **kwargs):
        assert kwargs == {'offset': 1, 'limit': 1}
        return 3, [{'txid': 'b'}]

    monkeypatch.setattr(esplora_api, 'get_transactions', fake_get_transactions)
    monkeypatch.setattr(esplora_api, 'parse_tx', lambda tx: fetched_ids.append(tx['txid']) or tx)

    params = TxHistoryParams(address='test-address', offset=1, limit=1)
    result = await client.get_transactions(params)
    assert result.total == 3
    assert fetched_ids == ['b']
    assert result.txs == [{'txid': 'b'}]


@pytest.mark.asyncio
async def test_transfer_rejects_invalid_recipient_without_network(monkeypatch):
    client = new_client()
    with pytest.raises(ValueError, match='Invalid address'):
        await client.transfer(BitcoinTxParams(amount=0.01, recipient='not-an-address', fee_rate=1))


@pytest.mark.asyncio
async def test_transfer_does_not_broadcast_when_signatures_invalid(monkeypatch):
    client = new_client()

    class FakeTransaction:
        def sign(self, private_key):
            pass

        def verify(self):
            return False

    async def fake_build_tx(**kwargs):
        return FakeTransaction(), []

    async def cannot_broadcast(*args):
        raise AssertionError('Network broadcast must not happen')

    monkeypatch.setattr(bitcoin_utils, 'build_tx', fake_build_tx)
    monkeypatch.setattr(bitcoin_utils, 'broadcast_tx', cannot_broadcast)
    recipient = client.get_address(1)
    with pytest.raises(ValueError, match='did not verify'):
        await client.transfer(BitcoinTxParams(amount=0.01, recipient=recipient, wallet_index=1, fee_rate=1))
