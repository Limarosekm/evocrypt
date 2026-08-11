import pytest

from cryptography.exceptions import InvalidTag

from evocrypt.crypto import (
    AESGCMCipher,
    generate_aes_key,
    KeyManager,
    PQCProvider,
    PQCNotAvailableError,
    HybridPQCProvider,
)


# ============================================================
# AES KEY GENERATION
# ============================================================

def test_aes_key_is_256_bit():

    key = generate_aes_key()

    assert isinstance(
        key,
        bytes
    )

    assert len(key) == 32


# ============================================================
# AES ENCRYPTION / DECRYPTION
# ============================================================

def test_aes_encrypt_decrypt():

    key = generate_aes_key()

    cipher = AESGCMCipher(
        key
    )

    plaintext = (
        b"EvoCrypt protected data"
    )

    result = cipher.encrypt(
        plaintext
    )

    decrypted = cipher.decrypt(

        result["ciphertext"],

        result["nonce"]
    )

    assert (
        decrypted
        == plaintext
    )


# ============================================================
# DIFFERENT NONCE
# ============================================================

def test_each_encryption_uses_new_nonce():

    key = generate_aes_key()

    cipher = AESGCMCipher(
        key
    )

    first = cipher.encrypt(
        b"same data"
    )

    second = cipher.encrypt(
        b"same data"
    )

    assert (
        first["nonce"]
        != second["nonce"]
    )


# ============================================================
# STRING ENCRYPTION
# ============================================================

def test_encrypt_text():

    key = generate_aes_key()

    cipher = AESGCMCipher(
        key
    )

    encrypted = cipher.encrypt_text(
        "Hello EvoCrypt",
        associated_data="session-1"
    )

    decrypted = cipher.decrypt_text(

        encrypted["ciphertext"],

        encrypted["nonce"],

        associated_data="session-1"
    )

    assert (
        decrypted
        == "Hello EvoCrypt"
    )


# ============================================================
# ASSOCIATED DATA
# ============================================================

def test_wrong_associated_data_fails():

    key = generate_aes_key()

    cipher = AESGCMCipher(
        key
    )

    encrypted = cipher.encrypt_text(

        "protected message",

        associated_data="session-1"
    )

    with pytest.raises(
        InvalidTag
    ):

        cipher.decrypt_text(

            encrypted["ciphertext"],

            encrypted["nonce"],

            associated_data="session-2"
        )


# ============================================================
# TAMPER DETECTION
# ============================================================

def test_modified_ciphertext_fails():

    key = generate_aes_key()

    cipher = AESGCMCipher(
        key
    )

    encrypted = cipher.encrypt(
        b"protected data"
    )

    modified = bytearray(
        encrypted["ciphertext"]
    )

    modified[0] ^= 1

    with pytest.raises(
        InvalidTag
    ):

        cipher.decrypt(

            bytes(modified),

            encrypted["nonce"]
        )


# ============================================================
# INVALID KEY SIZE
# ============================================================

def test_invalid_aes_key_size():

    with pytest.raises(
        ValueError
    ):

        AESGCMCipher(
            b"short-key"
        )


# ============================================================
# KEY MANAGER
# ============================================================

def test_key_manager_creates_key():

    manager = KeyManager(
        rotation_seconds=900
    )

    key = manager.create_key(
        "session-1"
    )

    assert (
        key.version
        == 1
    )

    assert key.active

    assert len(
        key.key
    ) == 32


# ============================================================
# KEY ROTATION
# ============================================================

def test_key_rotation():

    manager = KeyManager()

    first = manager.create_key(
        "session-1"
    )

    old_key = first.key

    second = manager.rotate(
        "session-1"
    )

    assert (
        second.version
        == 2
    )

    assert (
        second.key
        != old_key
    )

    assert second.active


# ============================================================
# KEY VERSION
# ============================================================

def test_multiple_key_rotations():

    manager = KeyManager()

    manager.create_key(
        "session-1"
    )

    manager.rotate(
        "session-1"
    )

    manager.rotate(
        "session-1"
    )

    manager.rotate(
        "session-1"
    )

    status = manager.status(
        "session-1"
    )

    assert (
        status["version"]
        == 4
    )

    assert (
        status["rotation_count"]
        == 3
    )


# ============================================================
# KEY FINGERPRINT
# ============================================================

def test_key_fingerprint_does_not_expose_key():

    manager = KeyManager()

    manager.create_key(
        "session-1"
    )

    fingerprint = (
        manager.fingerprint(
            "session-1"
        )
    )

    raw_key = manager.get_raw_key(
        "session-1"
    )

    assert fingerprint != (
        raw_key.hex()
    )

    assert len(
        fingerprint
    ) == 16


# ============================================================
# PQC PROVIDER
# ============================================================

def test_pqc_provider_is_not_available_by_default():

    provider = PQCProvider()

    assert (
        provider.available()
        is False
    )


# ============================================================
# PQC REQUIRES REAL PROVIDER
# ============================================================

def test_pqc_without_provider_raises():

    provider = PQCProvider()

    with pytest.raises(
        PQCNotAvailableError
    ):

        provider.generate_kem_keypair()


# ============================================================
# HYBRID PQC STATUS
# ============================================================

def test_hybrid_pqc_status():

    provider = HybridPQCProvider()

    status = provider.status()

    assert (
        status["available"]
        is False
    )

    assert (
        status["kem"]
        == "ML-KEM"
    )

    assert (
        status["signature"]
        == "ML-DSA"
    )