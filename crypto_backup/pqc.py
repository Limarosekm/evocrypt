class PQCProviderUnavailable(Exception):
    pass


class MLKEMProvider:
    """
    ML-KEM provider abstraction.

    The rest of EvoCrypt does not depend directly on
    a particular PQC library.
    """

    def __init__(self):
        self.available = False
        self.oqs = None

        try:
            import oqs

            self.oqs = oqs
            self.available = True

        except ImportError:
            self.available = False

    def generate_keypair(self):
        if not self.available:
            raise PQCProviderUnavailable(
                "ML-KEM provider is not installed."
            )

        kem = self.oqs.KeyEncapsulation(
            "ML-KEM-768"
        )

        public_key = kem.generate_keypair()

        secret_key = kem.export_secret_key()

        return {
            "public_key": public_key,
            "secret_key": secret_key,
        }

    def encapsulate(self, public_key):
        if not self.available:
            raise PQCProviderUnavailable(
                "ML-KEM provider is not installed."
            )

        kem = self.oqs.KeyEncapsulation(
            "ML-KEM-768"
        )

        ciphertext, shared_secret = (
            kem.encap_secret(public_key)
        )

        return {
            "ciphertext": ciphertext,
            "shared_secret": shared_secret,
        }

    def decapsulate(
        self,
        secret_key,
        ciphertext,
    ):
        if not self.available:
            raise PQCProviderUnavailable(
                "ML-KEM provider is not installed."
            )

        kem = self.oqs.KeyEncapsulation(
            "ML-KEM-768"
        )

        # Provider-specific implementation may differ.
        return kem.decap_secret(ciphertext)