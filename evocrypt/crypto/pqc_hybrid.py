
"""ML-KEM-768 + HKDF-SHA256 + AES-256-GCM hybrid encryption."""

from dataclasses import dataclass
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pqcrypto.kem import ml_kem_768


@dataclass(frozen=True)
class HybridEnvelope:
    kem_ciphertext: bytes
    salt: bytes
    nonce: bytes
    ciphertext: bytes


class PQCHybridEncryption:
    """Post-quantum key establishment with authenticated encryption."""

    @staticmethod
    def generate_keypair():
        """Return (public_key, private_key). Keep the private key secret."""
        return ml_kem_768.keygen()

    @staticmethod
    def _derive_aes_key(shared_secret: bytes, salt: bytes) -> bytes:
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"EvoCrypt-ML-KEM-768-AES-256-GCM-v1",
        ).derive(shared_secret)

    @classmethod
    def encrypt(
        cls,
        public_key: bytes,
        plaintext: bytes,
        associated_data: bytes = b"",
    ) -> HybridEnvelope:
        """Encrypt bytes for the owner of the ML-KEM public key."""
        kem_ciphertext, shared_secret = ml_kem_768.encaps(public_key)

        salt = os.urandom(16)
        nonce = os.urandom(12)
        aes_key = cls._derive_aes_key(shared_secret, salt)

        encrypted = AESGCM(aes_key).encrypt(
            nonce, plaintext, associated_data
        )

        return HybridEnvelope(
            kem_ciphertext=kem_ciphertext,
            salt=salt,
            nonce=nonce,
            ciphertext=encrypted,
        )

    @classmethod
    def decrypt(
        cls,
        private_key: bytes,
        envelope: HybridEnvelope,
        associated_data: bytes = b"",
    ) -> bytes:
        """Recover plaintext; authentication failures raise InvalidTag."""
        shared_secret = ml_kem_768.decaps(
            private_key, envelope.kem_ciphertext
        )
        aes_key = cls._derive_aes_key(shared_secret, envelope.salt)

        return AESGCM(aes_key).decrypt(
            envelope.nonce,
            envelope.ciphertext,
            associated_data,
        )
