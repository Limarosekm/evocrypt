"""Post-quantum provider abstractions, optional liboqs-python backend."""


class PQCNotAvailableError(RuntimeError):
    pass


class PQCProvider:
    """Compatibility wrapper for optional ML-KEM support."""

    def __init__(self):
        self._provider = None
        try:
            from .pqc_backend import OQSPQCBackend  # optional project-specific backend
            self._provider = OQSPQCBackend()
        except (ImportError, ModuleNotFoundError):
            try:
                import oqs
                self._oqs = oqs
                self._provider = "oqs"
            except ImportError:
                self._oqs = None

    def available(self):
        return self._provider is not None

    def generate_kem_keypair(self):
        if not self.available():
            raise PQCNotAvailableError("ML-KEM provider is not installed.")
        if self._provider == "oqs":
            with self._oqs.KeyEncapsulation("ML-KEM-768") as kem:
                public_key = kem.generate_keypair()
                secret_key = kem.export_secret_key()
                return {"public_key": public_key, "secret_key": secret_key}
        return self._provider.generate_kem_keypair()


class HybridPQCProvider:
    """Status abstraction for the project's planned hybrid PQC path."""

    def __init__(self):
        self._provider = PQCProvider()

    def status(self):
        return {
            "available": self._provider.available(),
            "kem": "ML-KEM",
            "signature": "ML-DSA",
        }


# Keep the project's original provider name available for existing imports.
class PQCProviderUnavailable(PQCNotAvailableError):
    pass


class MLKEMProvider:
    """Backward-compatible ML-KEM provider API used by the current project."""

    def __init__(self):
        self.available = False
        self.oqs = None
        try:
            import oqs
            self.oqs = oqs
            self.available = True
        except ImportError:
            pass

    def generate_keypair(self):
        if not self.available:
            raise PQCProviderUnavailable("ML-KEM provider is not installed.")
        with self.oqs.KeyEncapsulation("ML-KEM-768") as kem:
            public_key = kem.generate_keypair()
            secret_key = kem.export_secret_key()
            return {"public_key": public_key, "secret_key": secret_key}

    def encapsulate(self, public_key):
        if not self.available:
            raise PQCProviderUnavailable("ML-KEM provider is not installed.")
        with self.oqs.KeyEncapsulation("ML-KEM-768") as kem:
            ciphertext, shared_secret = kem.encap_secret(public_key)
            return {"ciphertext": ciphertext, "shared_secret": shared_secret}

    def decapsulate(self, secret_key, ciphertext):
        if not self.available:
            raise PQCProviderUnavailable("ML-KEM provider is not installed.")
        with self.oqs.KeyEncapsulation("ML-KEM-768", secret_key) as kem:
            return kem.decap_secret(ciphertext)
