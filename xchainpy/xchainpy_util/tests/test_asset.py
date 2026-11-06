import pytest
from xchainpy_util.asset import Asset

class TestAsset:

    def test_create_asset(self):
        asset = Asset('ETH', 'USDT-0x1234')
        assert asset.chain == 'ETH'
        assert asset.symbol == 'USDT-0x1234'
        assert asset.ticker == 'USDT'

    def test_invalid_chain(self):
        with pytest.raises(Exception) as err:
            Asset('invalid chain', 'BTC', 'BTC')
        assert str(err.value) == "the chain is invalid"

    def test_asset_to_string(self):
        asset = Asset('ETH', 'USDT-0x1234', 'USDT')
        assert str(asset) == 'ETH.USDT-0x1234'

    def test_asset_equal(self):
        asset = Asset('ETH', 'USDT-0x1234', 'USDT')
        asset2 = Asset('ETH', 'USDT-0x1234', 'USDT')
        assert asset == asset2
