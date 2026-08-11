import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from .classical import generate_aes_key


@dataclass
class SessionKey:
    """
    Represents one cryptographic key version.
    """

    session_id: str

    version: int

    key: bytes

    created_at: datetime

    active: bool = True


class KeyManager:
    """
    EvoCrypt session-key manager.

    Responsibilities:

        - Generate session keys
        - Track key versions
        - Rotate keys
        - Expose key metadata
        - Remove session keys

    Keys are held in memory for the demo/framework
    prototype. Production deployments should use a
    hardened key-management system or KMS/HSM.
    """

    def __init__(
        self,
        rotation_seconds: int = 900
    ):
        self.rotation_seconds = int(
            rotation_seconds
        )

        self._keys: Dict[
            str,
            SessionKey
        ] = {}

    # ============================================================
    # CREATE KEY
    # ============================================================

    def create_key(
        self,
        session_id: str
    ) -> SessionKey:
        """
        Create the first key for a session.
        """

        if not session_id:

            raise ValueError(
                "session_id is required"
            )

        if session_id in self._keys:

            raise ValueError(
                "Key already exists for session"
            )

        key = SessionKey(

            session_id=session_id,

            version=1,

            key=generate_aes_key(),

            created_at=datetime.now(
                timezone.utc
            ),

            active=True
        )

        self._keys[
            session_id
        ] = key

        return key

    # ============================================================
    # GET KEY
    # ============================================================

    def get_key(
        self,
        session_id: str
    ) -> SessionKey:
        """
        Return the active key for a session.
        """

        key = self._keys.get(
            session_id
        )

        if key is None:

            raise KeyError(
                f"No key for session: {session_id}"
            )

        if not key.active:

            raise RuntimeError(
                "Session key is inactive"
            )

        return key

    # ============================================================
    # RAW KEY
    # ============================================================

    def get_raw_key(
        self,
        session_id: str
    ) -> bytes:
        """
        Return the raw AES key.

        This should only be used internally by the
        EvoCrypt crypto layer.
        """

        return self.get_key(
            session_id
        ).key

    # ============================================================
    # ROTATE KEY
    # ============================================================

    def rotate(
        self,
        session_id: str
    ) -> SessionKey:
        """
        Rotate the active session key.

        The old key is marked inactive and a fresh
        256-bit AES key is generated.
        """

        old_key = self.get_key(
            session_id
        )

        old_key.active = False

        new_key = SessionKey(

            session_id=session_id,

            version=(
                old_key.version + 1
            ),

            key=generate_aes_key(),

            created_at=datetime.now(
                timezone.utc
            ),

            active=True
        )

        self._keys[
            session_id
        ] = new_key

        return new_key

    # ============================================================
    # SHOULD ROTATE?
    # ============================================================

    def should_rotate(
        self,
        session_id: str
    ) -> bool:
        """
        Determine whether the current key has exceeded
        the configured rotation interval.
        """

        key = self.get_key(
            session_id
        )

        now = datetime.now(
            timezone.utc
        )

        age = (
            now -
            key.created_at
        ).total_seconds()

        return (
            age >=
            self.rotation_seconds
        )

    # ============================================================
    # ENSURE FRESH KEY
    # ============================================================

    def ensure_fresh_key(
        self,
        session_id: str
    ) -> SessionKey:
        """
        Return the current key.

        Automatically rotates it if the configured
        key lifetime has expired.
        """

        if self.should_rotate(
            session_id
        ):

            return self.rotate(
                session_id
            )

        return self.get_key(
            session_id
        )

    # ============================================================
    # KEY AGE
    # ============================================================

    def age_seconds(
        self,
        session_id: str
    ) -> float:

        key = self.get_key(
            session_id
        )

        now = datetime.now(
            timezone.utc
        )

        return max(
            0.0,
            (
                now -
                key.created_at
            ).total_seconds()
        )

    # ============================================================
    # KEY FINGERPRINT
    # ============================================================

    def fingerprint(
        self,
        session_id: str
    ) -> str:
        """
        Return a non-reversible identifier for the
        current key.

        The actual key is never returned.
        """

        key = self.get_raw_key(
            session_id
        )

        digest = hashlib.sha256(
            key
        ).hexdigest()

        return digest[:16]

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
        session_id: str
    ) -> dict:
        """
        Return safe key metadata.

        The actual key material is never exposed.
        """

        key = self.get_key(
            session_id
        )

        return {

            "version":
                key.version,

            "age_seconds":
                round(
                    self.age_seconds(
                        session_id
                    ),
                    2
                ),

            "rotation_seconds":
                self.rotation_seconds,

            "rotation_count":
                max(
                    0,
                    key.version - 1
                ),

            "fingerprint":
                self.fingerprint(
                    session_id
                )
        }

    # ============================================================
    # DELETE KEY
    # ============================================================

    def remove(
        self,
        session_id: str
    ) -> bool:
        """
        Remove key material for a session.
        """

        key = self._keys.get(
            session_id
        )

        if key is None:

            return False

        key.active = False

        del self._keys[
            session_id
        ]

        return True

    # ============================================================
    # SESSION COUNT
    # ============================================================

    def count(self) -> int:

        return len(
            self._keys
        )