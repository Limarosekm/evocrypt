import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


AES_KEY_SIZE = 32
NONCE_SIZE = 12


def generate_aes_key() -> bytes:
    """
    Generate a fresh 256-bit AES key.

    Returns:
        32-byte AES key.
    """

    return AESGCM.generate_key(
        bit_length=256
    )


class AESGCMCipher:
    """
    AES-256-GCM encryption helper.

    EvoCrypt uses this class for the currently
    implemented classical encryption mode.

    AES-GCM provides:

        Confidentiality
        +
        Integrity
        +
        Authentication
    """

    def __init__(
        self,
        key: bytes
    ):
        """
        Initialize the cipher with a 256-bit key.

        Args:
            key:
                Exactly 32 bytes.
        """

        if not isinstance(
            key,
            bytes
        ):
            raise TypeError(
                "AES key must be bytes"
            )

        if len(key) != AES_KEY_SIZE:
            raise ValueError(
                "AES-256-GCM requires "
                "a 32-byte key"
            )

        self.key = key

        self._cipher = AESGCM(
            self.key
        )

    # ============================================================
    # ENCRYPT
    # ============================================================

    def encrypt(
        self,
        plaintext: bytes,
        associated_data: Optional[bytes] = None
    ) -> dict:
        """
        Encrypt plaintext using AES-256-GCM.

        A fresh random nonce is generated for every
        encryption operation.

        Returns:

            {
                "ciphertext": bytes,
                "nonce": bytes
            }
        """

        if not isinstance(
            plaintext,
            bytes
        ):
            raise TypeError(
                "plaintext must be bytes"
            )

        nonce = os.urandom(
            NONCE_SIZE
        )

        ciphertext = self._cipher.encrypt(
            nonce,
            plaintext,
            associated_data
        )

        return {
            "ciphertext": ciphertext,
            "nonce": nonce
        }

    # ============================================================
    # DECRYPT
    # ============================================================

    def decrypt(
        self,
        ciphertext: bytes,
        nonce: bytes,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Decrypt AES-GCM ciphertext.

        Raises:
            ValueError:
                If the nonce is invalid.

            cryptography.exceptions.InvalidTag:
                If ciphertext integrity verification fails.
        """

        if not isinstance(
            ciphertext,
            bytes
        ):
            raise TypeError(
                "ciphertext must be bytes"
            )

        if not isinstance(
            nonce,
            bytes
        ):
            raise TypeError(
                "nonce must be bytes"
            )

        if len(nonce) != NONCE_SIZE:
            raise ValueError(
                "AES-GCM nonce must be "
                "12 bytes"
            )

        return self._cipher.decrypt(
            nonce,
            ciphertext,
            associated_data
        )

    # ============================================================
    # STRING ENCRYPTION
    # ============================================================

    def encrypt_text(
        self,
        plaintext: str,
        associated_data: Optional[str] = None
    ) -> dict:
        """
        Encrypt a UTF-8 string.

        Returns base64 encoded values so that the
        result can easily be transferred through JSON.
        """

        if not isinstance(
            plaintext,
            str
        ):
            raise TypeError(
                "plaintext must be a string"
            )

        aad = None

        if associated_data is not None:

            aad = associated_data.encode(
                "utf-8"
            )

        result = self.encrypt(
            plaintext.encode(
                "utf-8"
            ),
            aad
        )

        return {
            "ciphertext": self._encode(
                result["ciphertext"]
            ),

            "nonce": self._encode(
                result["nonce"]
            )
        }

    # ============================================================
    # STRING DECRYPTION
    # ============================================================

    def decrypt_text(
        self,
        ciphertext: str,
        nonce: str,
        associated_data: Optional[str] = None
    ) -> str:
        """
        Decrypt base64 encoded AES-GCM ciphertext.
        """

        aad = None

        if associated_data is not None:

            aad = associated_data.encode(
                "utf-8"
            )

        plaintext = self.decrypt(
            self._decode(
                ciphertext
            ),

            self._decode(
                nonce
            ),

            aad
        )

        return plaintext.decode(
            "utf-8"
        )

    # ============================================================
    # BASE64 HELPERS
    # ============================================================

    @staticmethod
    def _encode(
        value: bytes
    ) -> str:

        return base64.urlsafe_b64encode(
            value
        ).decode(
            "ascii"
        )

    @staticmethod
    def _decode(
        value: str
    ) -> bytes:

        return base64.urlsafe_b64decode(
            value.encode(
                "ascii"
            )
        )