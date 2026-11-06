import httpx


async def broadcast_tx(blockstream_url, network, tx_hex):
    """Broadcast transaction
    https://github.com/Blockstream/esplora/blob/master/API.md#post-tx

    :param blockstream_url: blockstream url
    :type blockstream_url: str
    :param network: testnet or mainnet
    :type network: str
    :param tx_hex: tranaction hex
    :type tx_hex: str
    :returns: Transaction ID
    """
    from .esplora_api import api_base_url

    if not isinstance(tx_hex, str) or not tx_hex or len(tx_hex) % 2:
        raise ValueError('Transaction must be a non-empty even-length hex string')
    try:
        bytes.fromhex(tx_hex)
    except ValueError as exc:
        raise ValueError('Transaction must contain valid hexadecimal characters') from exc

    url = f'{api_base_url(blockstream_url, network)}/tx'
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, content=tx_hex, headers={'Content-Type': 'text/plain'})
        response.raise_for_status()
        return response.text.strip()
