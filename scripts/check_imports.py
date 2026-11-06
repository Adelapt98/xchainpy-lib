"""Import smoke test for the intentionally supported baseline packages.

This intentionally does not connect to any RPC or load wallet files.
"""

from xchainpy_util.asset import AssetBTC
from xchainpy_crypto import crypto
from xchainpy_client.base_xchain_client import BaseXChainClient
from xchainpy_bitcoin.client import Client as BitcoinClient
from xchainpy_litecoin.client import Client as LitecoinClient
from xchainpy_bitcoincash.client import Client as BitcoinCashClient
from xchainpy_ethereum.client import Client as EthereumClient

assert AssetBTC.ticker == 'BTC'
assert callable(crypto.generate_mnemonic)
assert all((BaseXChainClient, BitcoinClient, LitecoinClient, BitcoinCashClient, EthereumClient))

print('All seven supported baseline packages import successfully.')
