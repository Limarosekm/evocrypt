from dataclasses import dataclass


@dataclass(frozen=True)
class CryptoPolicy:
    """
    Cryptographic protection selected by EvoCrypt.
    """

    mode: str
    key_exchange: str
    cipher: str
    rotation_interval: int

    @property
    def pqc_enabled(self):
        return self.mode == "HYBRID_PQC"

    def to_dict(self):
        return {
            "mode": self.mode,
            "key_exchange": self.key_exchange,
            "cipher": self.cipher,
            "rotation_interval": self.rotation_interval,
            "pqc_enabled": self.pqc_enabled,
        }


class CryptoPolicyResolver:
    """
    Maps EvoCrypt security decisions to cryptographic policies.

    RL decides the security action.
    This class translates that action into crypto protection.
    """

    def __init__(self, pqc_enabled=True):
        self.pqc_enabled = bool(pqc_enabled)

    def resolve(self, trust_score, action):

        try:
            trust_score = float(trust_score)
        except (TypeError, ValueError):
            trust_score = 0.0

        action = str(
            action or "MONITOR"
        ).upper()

        # ======================================================
        # CRITICAL
        # ======================================================

        if (
            trust_score < 20
            or action == "TERMINATE_SESSION"
        ):
            return CryptoPolicy(
                mode="TERMINATE",
                key_exchange="NONE",
                cipher="NONE",
                rotation_interval=0,
            )

        # ======================================================
        # HIGH RISK / PQC
        # ======================================================

        if (
            trust_score < 40
            or action == "HYBRID_PQC"
        ):

            if self.pqc_enabled:

                return CryptoPolicy(
                    mode="HYBRID_PQC",
                    key_exchange="ML-KEM-768",
                    cipher="AES-256-GCM",
                    rotation_interval=60,
                )

            return CryptoPolicy(
                mode="PQC-READY",
                key_exchange="NONE",
                cipher="AES-256-GCM",
                rotation_interval=60,
            )

        # ======================================================
        # MEDIUM RISK
        # ======================================================

        if (
            trust_score < 70
            or action in {
                "MONITOR",
                "ROTATE_KEY",
                "REAUTHENTICATE",
            }
        ):
            return CryptoPolicy(
                mode="MONITOR_ROTATE",
                key_exchange="NONE",
                cipher="AES-256-GCM",
                rotation_interval=300,
            )

        # ======================================================
        # NORMAL
        # ======================================================

        return CryptoPolicy(
            mode="NORMAL",
            key_exchange="NONE",
            cipher="AES-256-GCM",
            rotation_interval=900,
        )