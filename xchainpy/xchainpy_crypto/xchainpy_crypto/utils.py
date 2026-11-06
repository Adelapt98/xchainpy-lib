import asyncio
from Crypto.Protocol.KDF import PBKDF2


async def pbkdf2(passphrase, salt, iterations, keylen, digest):
    # asyncio.coroutine was removed in Python 3.11. Offload PBKDF2 so an
    # expensive key derivation does not block an application's event loop.
    return await asyncio.to_thread(
        PBKDF2,
        password=passphrase,
        salt=salt,
        count=iterations,
        dkLen=keylen,
        hmac_hash_module=digest,
    )
