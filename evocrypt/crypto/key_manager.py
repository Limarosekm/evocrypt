"""In-memory session key manager with legacy and compatibility APIs."""
import hashlib
import secrets
import time
from dataclasses import dataclass


@dataclass
class ManagedKey:
    key: bytes
    version: int
    active: bool = True
    created_at: float = 0.0


class KeyManager:
    """Keeps ephemeral 256-bit session keys in memory."""

    def __init__(self, rotation_seconds=None):
        self._keys = {}
        self._rotation_counts = {}
        self.rotation_seconds = rotation_seconds

    def generate_key(self, session_id: str):
        """Legacy API used by the existing adaptive engine; returns a dict."""
        previous = self._keys.get(session_id, {})
        version = previous.get("version", 0) + 1
        key = secrets.token_bytes(32)
        record = {"key": key, "created_at": time.time(), "version": version}
        self._keys[session_id] = record
        if version > 1:
            self._rotation_counts[session_id] = self._rotation_counts.get(session_id, 0) + 1
        else:
            self._rotation_counts.setdefault(session_id, 0)
        return record

    def get_key(self, session_id: str):
        return self._keys.get(session_id)

    def rotate_key(self, session_id: str):
        return self.generate_key(session_id)

    def delete_key(self, session_id: str):
        self._keys.pop(session_id, None)
        self._rotation_counts.pop(session_id, None)

    def needs_rotation(self, session_id: str, interval: int) -> bool:
        if interval <= 0:
            return False
        record = self.get_key(session_id)
        if record is None:
            return True
        return time.time() - record["created_at"] >= interval

    def clear(self):
        self._keys.clear()
        self._rotation_counts.clear()

    # Compatibility API expected by tests and other client code.
    def create_key(self, session_id: str) -> ManagedKey:
        record = self.generate_key(session_id)
        return ManagedKey(
            key=record["key"],
            version=record["version"],
            active=True,
            created_at=record["created_at"],
        )

    def rotate(self, session_id: str) -> ManagedKey:
        record = self.rotate_key(session_id)
        return ManagedKey(
            key=record["key"],
            version=record["version"],
            active=True,
            created_at=record["created_at"],
        )

    def status(self, session_id: str):
        record = self._keys.get(session_id)
        if record is None:
            return {"version": 0, "rotation_count": 0, "active": False}
        return {
            "version": record["version"],
            "rotation_count": self._rotation_counts.get(session_id, 0),
            "active": True,
        }

    def get_raw_key(self, session_id: str):
        record = self._keys.get(session_id)
        return record["key"] if record else None

    def fingerprint(self, session_id: str):
        raw = self.get_raw_key(session_id)
        if raw is None:
            return None
        return hashlib.sha256(raw).hexdigest()[:16]
