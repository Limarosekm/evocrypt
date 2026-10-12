import os

from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM,
    ChaCha20Poly1305,
)


class ClassicalCrypto:

    AES_KEY_SIZE = 32
    NONCE_SIZE = 12

    @staticmethod
    def generate_aes_key():
        return os.urandom(
            ClassicalCrypto.AES_KEY_SIZE
        )

    @staticmethod
    def aes_encrypt(
        key,
        plaintext,
        associated_data=None,
    ):
        nonce = os.urandom(
            ClassicalCrypto.NONCE_SIZE
        )

        aes = AESGCM(key)

        ciphertext = aes.encrypt(
            nonce,
            plaintext,
            associated_data,
        )

        return {
            "nonce": nonce,
            "ciphertext": ciphertext,
        }

    @staticmethod
    def aes_decrypt(
        key,
        ciphertext,
        nonce,
        associated_data=None,
    ):
        aes = AESGCM(key)

        return aes.decrypt(
            nonce,
            ciphertext,
            associated_data,
        )

    @staticmethod
    def generate_chacha_key():
        return os.urandom(32)

    @staticmethod
    def chacha_encrypt(
        key,
        plaintext,
        associated_data=None,
    ):
        nonce = os.urandom(12)

        cipher = ChaCha20Poly1305(key)

        ciphertext = cipher.encrypt(
            nonce,
            plaintext,
            associated_data,
        )

        return {
            "nonce": nonce,
            "ciphertext": ciphertext,
        }

    @staticmethod
    def chacha_decrypt(
        key,
        ciphertext,
        nonce,
        associated_data=None,
    ):
        cipher = ChaCha20Poly1305(key)

        return cipher.decrypt(
            nonce,
            ciphertext,
            associated_data,
        )