
from .policy import CryptoPolicyResolver


class AdaptiveCryptoEngine:
    """
    EvoCrypt adaptive cryptographic policy engine.

    It works with the existing KeyManager.

    Responsibilities:

        Trust/RL decision
              ↓
        Crypto policy
              ↓
        Key rotation
              ↓
        Current crypto state
    """

    def __init__(
        self,
        key_manager,
        pqc_enabled=True,
    ):
        self.keys = key_manager

        self.policy_resolver = CryptoPolicyResolver(
            pqc_enabled=pqc_enabled
        )

        self._policies = {}

    # ==========================================================
    # INITIALIZE SESSION
    # ==========================================================

    def initialize_session(
        self,
        session_id,
        trust_score,
        action,
    ):
        """
        Create the initial cryptographic policy
        for a session.
        """

        policy = self.policy_resolver.resolve(
            trust_score,
            action,
        )

        self._policies[session_id] = policy

        return policy

    # ==========================================================
    # UPDATE POLICY
    # ==========================================================

    def update(
        self,
        session_id,
        trust_score,
        action,
    ):
        """
        Recalculate the cryptographic policy.

        If the security mode changes, the current
        session key is rotated automatically.
        """

        new_policy = self.policy_resolver.resolve(
            trust_score,
            action,
        )

        old_policy = self._policies.get(
            session_id
        )

        # ------------------------------------------------------
        # First policy
        # ------------------------------------------------------

        if old_policy is None:

            self._policies[session_id] = new_policy

            return {
                "policy": new_policy,
                "changed": True,
                "rotated": False,
            }

        # ------------------------------------------------------
        # Detect security-level change
        # ------------------------------------------------------

        changed = (
            old_policy.mode
            != new_policy.mode
        )

        rotated = False

        # ------------------------------------------------------
        # Automatically rotate when protection changes
        # ------------------------------------------------------

        if changed:

            if new_policy.mode != "TERMINATE":

                # KeyManager uses rotate_key()
                self.keys.rotate_key(
                    session_id
                )

                rotated = True

        # ------------------------------------------------------
        # Check time-based key rotation
        # ------------------------------------------------------

        elif new_policy.rotation_interval > 0:

            if self.keys.needs_rotation(
                session_id,
                new_policy.rotation_interval
            ):

                self.keys.rotate_key(
                    session_id
                )

                rotated = True

        # ------------------------------------------------------
        # Save current policy
        # ------------------------------------------------------

        self._policies[session_id] = new_policy

        return {
            "policy": new_policy,
            "changed": changed,
            "rotated": rotated,
        }

    # ==========================================================
    # GET POLICY
    # ==========================================================

    def get_policy(
        self,
        session_id,
    ):
        """
        Return the current cryptographic policy
        for a session.
        """

        return self._policies.get(
            session_id
        )

    # ==========================================================
    # STATUS
    # ==========================================================

    def status(
        self,
        session_id,
    ):
        """
        Return the current cryptographic policy
        as a dictionary.
        """

        policy = self._policies.get(
            session_id
        )

        if policy is None:

            return {
                "mode": "NONE",
                "cipher": "NONE",
                "key_exchange": "NONE",
                "rotation_interval": 0,
                "pqc_enabled": False,
            }

        return policy.to_dict()

    # ==========================================================
    # REMOVE SESSION
    # ==========================================================

    def remove_session(
        self,
        session_id,
    ):
        """
        Remove adaptive crypto state for a session.
        """

        self._policies.pop(
            session_id,
            None
        )

