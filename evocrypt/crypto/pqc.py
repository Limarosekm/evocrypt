from typing import Any, Dict, Optional


class PQCNotAvailableError(
    RuntimeError
):
    """
    Raised when a post-quantum provider has not
    been configured.
    """


class PQCProvider:
    """
    Abstract interface for a post-quantum provider.

    EvoCrypt uses this interface so that the core
    framework does not depend directly on one PQC
    library.

    A real provider can later implement:

        ML-KEM
        ML-DSA

    through this interface.
    """

    name = "abstract"

    def available(self) -> bool:
        """
        Return whether the PQC provider is available.
        """

        return False

    def generate_kem_keypair(
        self
    ):
        """
        Generate an ML-KEM keypair.

        Provider implementations must override this.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )

    def encapsulate(
        self,
        public_key: Any
    ):
        """
        Perform KEM encapsulation.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )

    def decapsulate(
        self,
        private_key: Any,
        ciphertext: Any
    ):
        """
        Perform KEM decapsulation.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )

    def generate_signature_keypair(
        self
    ):
        """
        Generate an ML-DSA signing keypair.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )

    def sign(
        self,
        private_key: Any,
        message: bytes
    ):
        """
        Generate a post-quantum signature.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )

    def verify(
        self,
        public_key: Any,
        message: bytes,
        signature: Any
    ) -> bool:
        """
        Verify a post-quantum signature.
        """

        raise PQCNotAvailableError(
            "No PQC provider is configured."
        )


class HybridPQCProvider:
    """
    Adapter for hybrid classical + post-quantum security.

    Concept:

        Classical key exchange
                +
        ML-KEM
                ↓
        Combined session secret

    The actual PQC implementation is supplied by
    an external validated provider.
    """

    def __init__(
        self,
        provider: Optional[PQCProvider] = None
    ):
        self.provider = (
            provider
            or PQCProvider()
        )

    # ============================================================
    # AVAILABILITY
    # ============================================================

    def available(
        self
    ) -> bool:

        return self.provider.available()

    # ============================================================
    # PROVIDER NAME
    # ============================================================

    @property
    def name(
        self
    ) -> str:

        return self.provider.name

    # ============================================================
    # REQUIRE PROVIDER
    # ============================================================

    def _require_provider(
        self
    ):

        if not self.available():

            raise PQCNotAvailableError(
                "A validated PQC provider is not "
                "configured. Install/configure an "
                "ML-KEM/ML-DSA provider before "
                "enabling production PQC."
            )

        return self.provider

    # ============================================================
    # ML-KEM
    # ============================================================

    def generate_kem_keypair(
        self
    ):

        provider = (
            self._require_provider()
        )

        return provider.generate_kem_keypair()

    def encapsulate(
        self,
        public_key: Any
    ):

        provider = (
            self._require_provider()
        )

        return provider.encapsulate(
            public_key
        )

    def decapsulate(
        self,
        private_key: Any,
        ciphertext: Any
    ):

        provider = (
            self._require_provider()
        )

        return provider.decapsulate(
            private_key,
            ciphertext
        )

    # ============================================================
    # ML-DSA
    # ============================================================

    def generate_signature_keypair(
        self
    ):

        provider = (
            self._require_provider()
        )

        return provider.generate_signature_keypair()

    def sign(
        self,
        private_key: Any,
        message: bytes
    ):

        provider = (
            self._require_provider()
        )

        return provider.sign(
            private_key,
            message
        )

    def verify(
        self,
        public_key: Any,
        message: bytes,
        signature: Any
    ) -> bool:

        provider = (
            self._require_provider()
        )

        return provider.verify(
            public_key,
            message,
            signature
        )

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self
    ) -> Dict[str, Any]:

        return {

            "available":
                self.available(),

            "provider":
                self.name,

            "kem":
                "ML-KEM",

            "signature":
                "ML-DSA"
        }