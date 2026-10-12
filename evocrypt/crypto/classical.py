"""Classical authenticated encryption primitives used by EvoCrypt."""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305


class ClassicalCrypto:
    AES_KEY_SIZE = 32
    NONCE_SIZE = 12

    @staticmethod
    def generate_aes_key():
        return os.urandom(ClassicalCrypto.AES_KEY_SIZE)

    @staticmethod
    def aes_encrypt(key, plaintext, associated_data=None):
        nonce = os.urandom(ClassicalCrypto.NONCE_SIZE)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
        return {"nonce": nonce, "ciphertext": ciphertext}

    @staticmethod
    def aes_decrypt(key, ciphertext, nonce, associated_data=None):
        return AESGCM(key).decrypt(nonce, ciphertext, associated_data)

    @staticmethod
    def generate_chacha_key():
        return os.urandom(32)

    @staticmethod
    def chacha_encrypt(key, plaintext, associated_data=None):
        nonce = os.urandom(12)
        ciphertext = ChaCha20Poly1305(key).encrypt(nonce, plaintext, associated_data)
        return {"nonce": nonce, "ciphertext": ciphertext}

    @staticmethod
    def chacha_decrypt(key, ciphertext, nonce, associated_data=None):
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, associated_data)


def generate_aes_key():
    """Compatibility API: return a fresh 256-bit AES key."""
    return ClassicalCrypto.generate_aes_key()


class AESGCMCipher:
    """Small object-oriented wrapper around AES-GCM with a fresh nonce per encryption."""

    def __init__(self, key):
        if not isinstance(key, bytes) or len(key) not in (16, 24, 32):
            raise ValueError("AES-GCM key must be 16, 24, or 32 bytes.")
        self._aes = AESGCM(key)

    def encrypt(self, plaintext, associated_data=None):
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        if isinstance(associated_data, str):
            associated_data = associated_data.encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = self._aes.encrypt(nonce, plaintext, associated_data)
        return {"nonce": nonce, "ciphertext": ciphertext}

    def decrypt(self, ciphertext, nonce, associated_data=None):
        if isinstance(associated_data, str):
            associated_data = associated_data.encode("utf-8")
        return self._aes.decrypt(nonce, ciphertext, associated_data)

    def encrypt_text(self, plaintext, associated_data=None):
        if not isinstance(plaintext, str):
            raise TypeError("plaintext must be a string")
        return self.encrypt(plaintext.encode("utf-8"), associated_data)

    def decrypt_text(self, ciphertext, nonce, associated_data=None):
        return self.decrypt(ciphertext, nonce, associated_data).decode("utf-8")
