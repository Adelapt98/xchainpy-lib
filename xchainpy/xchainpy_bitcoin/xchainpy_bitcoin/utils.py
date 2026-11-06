import binascii
from bitcoinlib.keys import Address
from typing import List, Optional, Union
from .const import MIN_TX_FEE
from .models.common import DerivePath, UTXO
from . import blockstream_api, esplora_api
from bitcoinlib.services.services import *
from xchainpy_util.asset import AssetBTC
from xchainpy_client.fees import standard_fees, calc_fees
from xchainpy_client.models import tx_types
from xchainpy_client.models.types import FeesWithRates
from xchainpy_client.models.types import FeesWithRates
import datetime


TX_EMPTY_SIZE = 4 + 1 + 1 + 4  # 10
TX_INPUT_BASE = 32 + 4 + 1 + 4  # 41
TX_INPUT_PUBKEYHASH = 107
TX_OUTPUT_BASE = 8 + 1  # 9
TX_OUTPUT_PUBKEYHASH = 25
DUST_THRESHOLD = 1000


def get_default_fees_with_rates() -> FeesWithRates:
    """Get the default fees with rates

    :returns: The default fees and rates (FeesWithRates)
    """
    rates = standard_fees(20)
    rates.fastest = 50
    fees = calc_fees(rates, calc_fee)
    return FeesWithRates(fees, rates)

def get_default_fees() -> FeesWithRates:
    """Get the default fees

    :returns: The default fees (Fees)
    """
    fees = get_default_fees_with_rates().fees
    return fees


def parse_tx(tx) -> tx_types.TX:
    """Parse tx

    :param tx: The transaction to be parsed
    :type tx: str
    :returns: The transaction parsed from the binance tx
    """
    asset = AssetBTC
    tx_from = [tx_types.TxFrom(i['address'], i['value']) for i in tx['inputs']]
    tx_to = [tx_types.TxTo(i['address'], i['value']) for i in tx['outputs']]
    tx_date = datetime.datetime.fromtimestamp(tx['time'])
    tx_type = 'transfer'
    tx_hash = tx['txid']

    tx = tx_types.TX(asset, tx_from, tx_to, tx_date, tx_type, tx_hash)
    return tx


def calc_fee(fee_rate, memo=''):
    """Calculate fees based on fee rate and memo

    :param fee_rate: fee rate
    :type fee_rate: int
    :param memo: memo
    :type memo: str
    :returns: The calculated fees based on fee rate and the memo
    """
    compiled_memo = compile_memo(memo) if memo else None
    fee = get_fee([], fee_rate, compiled_memo)
    return fee


def compile_memo(memo: str):
    """Compile memo

    :param memo: The memo to be compiled
    :type memo: str
    :returns: The compiled memo
    """
    metadata = bytes(memo, 'utf-8')
    metadata_len = len(metadata)

    if metadata_len <= 75:
        payload = bytes((metadata_len,)) + metadata
    elif metadata_len <= 255:
        payload = b'\x4c' + bytes((metadata_len,)) + metadata
    elif metadata_len <= 65535:
        payload = b'\x4d' + metadata_len.to_bytes(2, 'little') + metadata
    else:
        raise ValueError('Memo exceeds the maximum OP_PUSHDATA2 size')

    return b'\x6a' + payload


def validate_address(network, address):
    """Validate the BTC address

    :param network: testnet or mainnet
    :type network: str
    :param address: address
    :type address: str
    :returns: True or False
    """
    try:
        address = Address.parse(address=address, network=(
            'bitcoin' if network == 'mainnet' else network))
        return True
    except:
        return False


def get_fee(inputs: List[UTXO], fee_rate: float, data: Optional[bytes]=None):
    """Get the transaction fee

    :param inputs: the UTXOs
    :type inputs: List[UTXO]
    :param fee_rate: the fee rate
    :type fee_rate: float
    :param data: The compiled memo (Optional)
    :type data: bytes
    :returns: The fee amount
    """
    lst_reduce = 0
    if len(inputs) > 0:
        for x in inputs:
            lst_reduce += TX_INPUT_BASE + \
                (len(x.witness_utxo.script)
                 if x.witness_utxo.script else TX_INPUT_PUBKEYHASH)

    sum = TX_EMPTY_SIZE + lst_reduce + \
        len(inputs) + TX_OUTPUT_BASE + TX_OUTPUT_PUBKEYHASH + \
        TX_OUTPUT_BASE + TX_OUTPUT_PUBKEYHASH
    if data:
        sum = sum + TX_OUTPUT_BASE + len(data)
    fee = sum * fee_rate
    result = fee if fee > MIN_TX_FEE else MIN_TX_FEE
    return result


async def scan_UTXOs(sochain_url, network, address, confirmed_only=True):
    """Scan native SegWit wallet UTXOs from Esplora.

    :param sochain_url: sochain url
    :type sochain_url: str
    :param network: testnet or mainnet
    :type network: str
    :param address: address
    :type address: str
    :param confirmed_only: By default is True, scan only confirmed UTXOs
    :type confirmed_only: bool
    :returns: The UTXOs of the given address
    """
    return await esplora_api.get_unspent_txs(sochain_url, network, address, confirmed_only)


async def get_change(sochain_url:str, value_out, network:str, address:str):
    """Get the balance changes amount

    :param sochain_url: sochain url
    :type sochain_url: str
    :param value_out: amount you wnat to transfer
    :type value_out: int
    :param network: testnet or mainnet
    :type network: str
    :param address: address
    :type address: str
    :returns: The UTXOs of the given address
    """
    try:
        balance = await get_balance(sochain_url, address, network)
        balance = round(balance[0].amount * 10 ** 8)
        change = 0
        if balance - value_out > DUST_THRESHOLD:
            change = balance - value_out
        return change
    except Exception as err:
        raise Exception(str(err))


async def build_tx(sochain_url, amount, recipient, memo, fee_rate, sender, network, spend_pending_UTXO=False):
    """Build transcation

    :param sochain_url: sochain url
    :type sochain_url: str
    :param amount: amount of BTC to transfer
    :type amount: int
    :param recipient: destination address
    :type recipient: str
    :param memo: optional memo for transaction
    :type memo: str
    :param fee_rate: fee rates for transaction
    :type fee_rate: int
    :param sender: sender's address
    :type sender: str
    :param network: testnet or mainnet
    :type network: str
    :param spend_pending_UTXO: By default is False, prevent spending uncomfirmed UTXOs
    :type spend_pending_UTXO: bool
    :returns: transaction
    """
    try:
        # search only confirmed UTXOs if pending UTXO is not allowed
        confirmed_only = not spend_pending_UTXO

        utxos = await scan_UTXOs(sochain_url, network, sender, confirmed_only)
        if len(utxos) == 0:
            raise Exception("No utxos to send")

        if not validate_address(network, recipient):
            raise Exception('Invalid address')
        
        fee_rate_whole = int(fee_rate)
        
        compiled_memo = None
        if memo:
            compiled_memo = compile_memo(memo)

        fee = get_fee(utxos, fee_rate_whole, compiled_memo)

        available = sum(i.witness_utxo.value for i in utxos)
        if fee + amount > available:
            raise Exception('Balance insufficient for transaction')

        t = Transaction(network='bitcoin' if network == 'mainnet' else 'testnet', witness_type='segwit')

        for i in utxos:
            script = bytes(i.witness_utxo.script)
            if len(script) != 22 or not script.startswith(b'\x00\x14'):
                raise ValueError('Cannot sign non-P2WPKH UTXO')
            t.add_input(prev_txid=i.hash, output_n=i.index,
                        value=i.witness_utxo.value, locking_script=script,
                        script_type='sig_pubkey', witness_type='segwit', public_hash=script[2:])

        t.add_output(address=recipient, value=amount)
        change = available - amount - fee
        if change < 0:
            raise ValueError('Selected UTXOs insufficient for transaction')
        if 0 < change <= DUST_THRESHOLD:
            change = 0  # Dust is included in the miner fee.
        
        if change > 0:
            
            t.add_output(address=sender, value=change)

        if compiled_memo:
            t.add_output(lock_script=compiled_memo, value=0)

        return t, utxos

    except Exception as err:
        raise Exception(str(err))


async def broadcast_tx(blockstream_url, network, tx_hex):
    """Broadcast the transaction

    :param sochain_url: sochain url
    :type sochain_url: str
    :param network: testnet or mainnet
    :type network: str
    :param tx_hex: tranaction hex
    :type tx_hex: str
    :returns: The transaction hash
    """
    return await blockstream_api.broadcast_tx(blockstream_url, network, tx_hex)


async def get_balance(sochain_url:str, address:str, network:str):
    """Get the BTC balance of a given address

    :param sochain_url: sochain url
    :type sochain_url: str
    :param address: BTC address
    :type address: str
    :param network: mainnet or testnet
    :type network: str
    :returns: The BTC balance of the address
    """
    return await esplora_api.get_balance(sochain_url, network, address)
