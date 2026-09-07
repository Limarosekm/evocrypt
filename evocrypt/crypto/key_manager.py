
import secrets
import time


class KeyManager:
    """
    Lightweight in-memory session key manager.

    Keys are deliberately ephemeral and stored only
    for the lifetime of the running application.
    """

    def __init__(self):
        """
        Initialize the key store.
        """

        self._keys = {}

    # =============================================================
    # KEY GENERATION
    # =============================================================

    def generate_key(
        self,
        session_id: str
    ):
        """
        Generate a new 256-bit session key.

        A new version is created every time the key
        is generated or rotated.
        """

        key = secrets.token_bytes(32)

        previous = self._keys.get(
            session_id,
            {}
        )

        version = (
            previous.get(
                "version",
                0
            ) + 1
        )

        self._keys[session_id] = {
            "key": key,
            "created_at": time.time(),
            "version": version,
        }

        return self._keys[session_id]

    # =============================================================
    # GET CURRENT KEY
    # =============================================================

    def get_key(
        self,
        session_id: str
    ):
        """
        Return the current key record for a session.

        Returns None if the session has no key.
        """

        return self._keys.get(
            session_id
        )

    # =============================================================
    # KEY ROTATION
    # =============================================================

    def rotate_key(
        self,
        session_id: str
    ):
        """
        Generate and assign a new session key.

        The key version is automatically incremented.
        """

        return self.generate_key(
            session_id
        )

    # =============================================================
    # DELETE SESSION KEY
    # =============================================================

    def delete_key(
        self,
        session_id: str
    ):
        """
        Delete the key associated with a session.
        """

        self._keys.pop(
            session_id,
            None
        )

    # =============================================================
    # CHECK ROTATION REQUIREMENT
    # =============================================================

    def needs_rotation(
        self,
        session_id: str,
        interval: int
    ) -> bool:
        """
        Determine whether the current session key
        has exceeded the supplied rotation interval.
        """

        if interval <= 0:
            return False

        record = self.get_key(
            session_id
        )

        # No key means a new key is required.
        if record is None:
            return True

        age = (
            time.time()
            - record["created_at"]
        )

        return age >= interval

    # =============================================================
    # CLEAR ALL KEYS
    # =============================================================

    def clear(self):
        """
        Remove all session keys.
        """

        self._keys.clear()

