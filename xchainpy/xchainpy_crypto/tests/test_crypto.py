from Crypto.Cipher import AES
import pytest
from xchainpy_crypto import crypto


class TestCrypto:

    # Note: This phrase is created by https://iancoleman.io/bip39/ and will never been used in a real-world
    phrase = 'REDACTED'
    phrase2 = 'REDACTED'
    def test_valid_phrase(self):
        assert crypto.validate_phrase(self.phrase) == True

    def test_invalid_phrase(self):
        assert crypto.validate_phrase('invalid phrase') == False

    @pytest.mark.asyncio
    async def test_export_keystore(self):
        password = 'thorchain'
        keystore = await crypto.encrypt_to_keystore(self.phrase , password)
        assert keystore.crypto.cipher == 'aes-128-ctr'
        assert keystore.crypto.kdf == 'pbkdf2'
        assert keystore.crypto.kdfparams.prf == 'hmac-sha256'
        assert keystore.crypto.kdfparams.c == 262144
        assert keystore.version == 1
        assert keystore.meta == 'xchain-keystore'
    
    @pytest.mark.asyncio
    async def test_import_keystore(self):
        password = 'thorchain'
        keystore = await crypto.encrypt_to_keystore(self.phrase2 , password)
        decrypted = await crypto.decrypt_from_keystore(keystore , password)
        assert decrypted == self.phrase2

