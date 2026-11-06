# `xchainpy/xchainpy-util`

Utitity helpers for XChain clients

## Modules (in alphabetical order)

- `asset` - Utilities for handling assets
- `chain` - Utilities for multi-chain

-----------

## Usage

```bash
pip install xchainpy_util
```

Asset
-----------------

```python
from xchainpy_util.asset import Asset

asset = Asset(chain='BNB', symbol='RUNE-67C')
print(asset.chain)
print(asset.symbol)
print(asset.ticker)

asset = Asset(chain='BTC', symbol='BTC', ticker='BTC')
print(asset)
 ```

Chain
-----------------

```python
from xchainpy_util import chain
from xchainpy_util.chain import Chain
is_chain = chain.is_chain(Chain.Bitcoin)
print(is_chain)

is_chain = chain.is_chain('BTC')
print(is_chain)
 ```
    

## Tests

These packages needed to run tests:

- pytest `pip install pytest`

How to run tests?

```bash
$ python -m pytest xchainpy/xchainpy_util/tests
```

