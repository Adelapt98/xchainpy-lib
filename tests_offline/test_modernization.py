"""Safe, isolated regression tests; never submit blockchain transactions."""

import asyncio
from types import SimpleNamespace

import pytest
from web3 import Web3

from xchainpy_bitcoin.utils import compile_memo as btc_memo
from xchainpy_bitcoin import utils as bitcoin_utils
from xchainpy_litecoin.utils import compile_memo as ltc_memo
from xchainpy_ethereum.client import Client as EthereumClient
from xchainpy_util.asset import AssetRuneERC20, AssetRuneERC20Testnet


@pytest.mark.parametrize("compile_memo", [btc_memo, ltc_memo])
@pytest.mark.parametrize("length", [0, 1, 75, 76, 255, 256, 65535])
def test_op_return_pushdata_encoding(compile_memo, length):
    encoded = compile_memo('x' * length)
    if length <= 75:
        expected = b'\x6a' + bytes([length])
    elif length <= 255:
        expected = b'\x6a\x4c' + bytes([length])
    else:
        expected = b'\x6a\x4d' + length.to_bytes(2, 'little')
    assert encoded == expected + (b'x' * length)


@pytest.mark.parametrize("compile_memo", [btc_memo, ltc_memo])
def test_op_return_memo_is_utf8_bytes(compile_memo):
    assert compile_memo('€') == b'\x6a\x03\xe2\x82\xac'
    with pytest.raises(ValueError):
        compile_memo('x' * 65536)


def test_mainnet_and_testnet_rune_assets_are_distinct():
    assert '3155ba85' in AssetRuneERC20.symbol.lower()
    assert 'd601c6a3' in AssetRuneERC20Testnet.symbol.lower()


def test_ethereum_explorer_uses_live_sepolia_testnet():
    client = object.__new__(EthereumClient)
    client.network = 'testnet'
    client.w3 = Web3()
    assert client.get_explorer_url() == 'https://sepolia.etherscan.io'
    assert client.validate_address('0x0000000000000000000000000000000000000001')
    client.network = 'mainnet'
    assert client.get_explorer_url() == 'https://etherscan.io'


def test_ethereum_rejects_unconvertible_websocket_provider():
    client = object.__new__(EthereumClient)
    with pytest.raises(ValueError, match='HTTP'):
        client.set_wss_provider('wss://custom.provider.example/ws')


def test_ethereum_etherscan_v2_getabi(monkeypatch, tmp_path):
    client = object.__new__(EthereumClient)
    client.network = 'testnet'
    client.etherscan_token = 'test-only'
    client.script_dir = str(tmp_path)
    request_calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'status': '1', 'result': '[]'}

    def fake_get(url, **kwargs):
        request_calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr('xchainpy_ethereum.client.requests.get', fake_get)
    address = '0x0000000000000000000000000000000000000001'
    assert asyncio.run(client.get_abi(address)) == []
    assert asyncio.run(client.get_abi(address)) == []  # cached, no new request
    assert len(request_calls) == 1
    assert request_calls[0][0] == 'https://api.etherscan.io/v2/api'
    assert request_calls[0][1]['params']['chainid'] == 11155111


@pytest.mark.parametrize('network,expected_bitcoinlib_name', [
    ('mainnet', 'bitcoin'),
    ('testnet', 'testnet'),
])
def test_bitcoin_transaction_network_mapping(monkeypatch, network, expected_bitcoinlib_name):
    actual = []
    fake_utxo = SimpleNamespace(hash='00' * 32, index=0,
                                witness_utxo=SimpleNamespace(script=b'\x00\x14' + b'\x11' * 20, value=10_000_000))

    class StubTransaction:
        def __init__(self, network, witness_type):
            actual.append((network, witness_type))

        def add_input(self, **kwargs):
            pass

        def add_output(self, **kwargs):
            pass

    async def fake_scan(*args, **kwargs):
        return [fake_utxo]

    async def fake_balance(*args, **kwargs):
        return [SimpleNamespace(amount=1)]

    async def fake_change(*args, **kwargs):
        return 0

    monkeypatch.setattr(bitcoin_utils, 'scan_UTXOs', fake_scan)
    monkeypatch.setattr(bitcoin_utils, 'get_balance', fake_balance)
    monkeypatch.setattr(bitcoin_utils, 'get_change', fake_change)
    monkeypatch.setattr(bitcoin_utils, 'validate_address', lambda *args: True)
    monkeypatch.setattr(bitcoin_utils, 'Transaction', StubTransaction)
    result, utxos = asyncio.run(bitcoin_utils.build_tx(
        sochain_url='unused', amount=50_000, recipient='unused', memo='',
        fee_rate=1, sender='unused', network=network))
    assert isinstance(result, StubTransaction)
    assert len(utxos) == 1
    assert actual == [(expected_bitcoinlib_name, 'segwit')]
