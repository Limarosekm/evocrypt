
from dataclasses import replace

import pytest
from cryptography.exceptions import InvalidTag

from evocrypt.crypto.pqc_hybrid import PQCHybridEncryption


def test_ml_kem_aes_roundtrip():
    public_key, private_key = PQCHybridEncryption.generate_keypair()
    message = b"EvoCrypt post-quantum test"
    aad = b"evocrypt-test-v1"

    envelope = PQCHybridEncryption.encrypt(public_key, message, aad)
    recovered = PQCHybridEncryption.decrypt(
        private_key, envelope, aad
    )

    assert recovered == message


def test_tampered_ciphertext_is_rejected():
    public_key, private_key = PQCHybridEncryption.generate_keypair()
    envelope = PQCHybridEncryption.encrypt(
        public_key, b"Secret message"
    )

    modified = replace(
        envelope,
        ciphertext=envelope.ciphertext[:-1]
        + bytes([envelope.ciphertext[-1] ^ 1]),
    )

    with pytest.raises(InvalidTag):
        PQCHybridEncryption.decrypt(private_key, modified)


def test_wrong_associated_data_is_rejected():
    public_key, private_key = PQCHybridEncryption.generate_keypair()
    envelope = PQCHybridEncryption.encrypt(
        public_key, b"Secret message", b"original-context"
    )

    with pytest.raises(InvalidTag):
        PQCHybridEncryption.decrypt(
            private_key, envelope, b"wrong-context"
        )


def test_wrong_private_key_is_rejected():
    public_key, _ = PQCHybridEncryption.generate_keypair()
    _, wrong_private_key = PQCHybridEncryption.generate_keypair()

    envelope = PQCHybridEncryption.encrypt(
        public_key, b"Secret message"
    )

    with pytest.raises(InvalidTag):
        PQCHybridEncryption.decrypt(wrong_private_key, envelope)
