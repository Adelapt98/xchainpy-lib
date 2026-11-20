"""Offline regression coverage for the shared XChainPy core contracts."""

import json

import pytest

from xchainpy_client.base_xchain_client import BaseXChainClient
from xchainpy_client.models.types import Network, RootDerivationPaths, XChainClientParams
from xchainpy_crypto import crypto
from xchainpy_util.chain import Chain


# A public, deterministic BIP39 test vector. Never use it for a funded wallet.
# Public BIP39 vectors: https://github.com/trezor/python-mnemonic/blob/master/vectors.json
TEST_PHRASE = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'


class DummyClient(BaseXChainClient):
    def get_address(self, index=0):
        return f'dummy-address-{index}'


def new_client(network=Network.Mainnet, phrase=None):
    paths = RootDerivationPaths(mainnet="m/84'/0'/0'/0/", testnet="m/84'/1'/0'/0/")
    return DummyClient(Chain.Bitcoin, XChainClientParams(
        network=network, phrase=phrase, root_derivation_paths=paths))


@pytest.mark.parametrize('network,path', [
    ('mainnet', "m/84'/0'/0'/0/7"),
    ('testnet', "m/84'/1'/0'/0/7"),
])
def test_full_derivation_path(network, path):
    client = new_client(network)
    assert client.get_full_derivation_path(7) == path


@pytest.mark.parametrize('index', [-1, True, 1.5, '0'])
def test_derivation_path_rejects_invalid_wallet_index(index):
    with pytest.raises(ValueError, match='wallet_index'):
        new_client().get_full_derivation_path(index)


@pytest.mark.parametrize('network', ['mainnet', 'testnet', 'MAINNET', Network.Mainnet])
def test_supported_networks(network):
    client = new_client(network)
    assert client.get_network() in ('mainnet', 'testnet')


def test_invalid_network_is_rejected():
    with pytest.raises(Exception, match='Invalid network'):
        new_client('deprecated-network')


def test_set_phrase_and_purge_client():
    client = new_client()
    assert client.set_phrase(TEST_PHRASE, wallet_index=3) == 'dummy-address-3'
    client.purge_client()
    assert client.phrase == ''
    with pytest.raises(Exception, match='invalid phrase'):
        client.set_phrase('not a valid phrase')


@pytest.mark.asyncio
async def test_thornode_http_client_closes_and_selects_network(monkeypatch):
    from xchainpy_client import base_xchain_client

    calls = []

    class FakeResponse:
        status_code = 200
        content = b'[{' + b'"chain":"BTC","gas_rate":"42"' + b'}]'

    class FakeHttpClient:
        def __init__(self, timeout):
            assert timeout == 5

        async def __aenter__(self):
            calls.append('open')
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            calls.append('close')

        async def get(self, url):
            calls.append(url)
            return FakeResponse()

    monkeypatch.setattr(base_xchain_client.httpx, 'AsyncClient', FakeHttpClient)

    client = new_client(Network.Mainnet)
    assert await client.get_fee_rate_from_thorchain() == 42.0
    client.set_network(Network.Testnet)
    assert await client.get_fee_rate_from_thorchain() == 42.0
    assert calls[0] == 'open' and calls[2] == 'close'
    assert calls[3] == 'open' and calls[5] == 'close'
    assert 'thornode.thorchain.info' in calls[1]
    assert 'testnet.thornode.thorchain.info' in calls[4]


@pytest.mark.asyncio
async def test_thornode_missing_chain_raises():
    client = new_client()

    async def fake_get(endpoint):
        return [{'chain': 'LTC', 'gas_rate': '12'}]

    client.thornode_api_get = fake_get
    with pytest.raises(Exception, match='does not contain fees for BTC'):
        await client.get_fee_rate_from_thorchain()


@pytest.mark.parametrize('size', [12, 15, 18, 21, 24])
def test_generated_mnemonic_lengths(size):
    phrase = crypto.generate_mnemonic(size=size)
    assert len(phrase.split()) == size
    assert crypto.validate_phrase(phrase)


@pytest.mark.parametrize('size', [0, 11, 13, 25, 12.0, None])
def test_reject_nonstandard_mnemonic_lengths(size):
    with pytest.raises(ValueError, match='mnemonic size'):
        crypto.generate_mnemonic(size=size)


@pytest.mark.asyncio
async def test_keystore_json_roundtrip_and_wrong_password():
    keystore = await crypto.encrypt_to_keystore(TEST_PHRASE, 'password-1')
    saved = json.loads(keystore.to_json())
    assert await crypto.decrypt_from_keystore(saved, 'password-1') == TEST_PHRASE
    with pytest.raises(Exception, match='Invalid Password'):
        await crypto.decrypt_from_keystore(saved, 'wrong-password')


@pytest.mark.asyncio
async def test_keystore_tamper_detection():
    keystore = await crypto.encrypt_to_keystore(TEST_PHRASE, 'password-2')
    saved = json.loads(keystore.to_json())
    saved['crypto']['mac'] = '0' * 64
    with pytest.raises(Exception, match='Invalid Password'):
        await crypto.decrypt_from_keystore(saved, 'password-2')
