from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class ManagedSession:
    """
    Internal representation of an EvoCrypt session.
    """

    session_id: str

    user_id: str

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    last_activity: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    active: bool = True

    metadata: Dict = field(
        default_factory=dict
    )

    termination_reason: Optional[str] = None


class SessionManager:
    """
    EvoCrypt session lifecycle manager.

    Responsibilities:

        - Create sessions
        - Track activity
        - Validate sessions
        - Refresh activity
        - Terminate sessions
        - Inspect session state

    The SessionManager does not decide whether a session
    should be trusted. That decision belongs to TrustScorer
    and AdaptivePolicyAgent.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        timeout_seconds: int = 1800
    ):
        """
        Initialize the session manager.

        Args:
            timeout_seconds:
                Maximum allowed inactivity period.
        """

        self.timeout_seconds = int(
            timeout_seconds
        )

        self._sessions: Dict[
            str,
            ManagedSession
        ] = {}

    # ============================================================
    # CREATE SESSION
    # ============================================================

    def create(
        self,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> ManagedSession:
        """
        Create a new managed session.

        Raises:
            ValueError if the session ID already exists.
        """

        if not session_id:

            raise ValueError(
                "session_id is required"
            )

        if not user_id:

            raise ValueError(
                "user_id is required"
            )

        if session_id in self._sessions:

            raise ValueError(
                f"Session already exists: {session_id}"
            )

        now = datetime.now(
            timezone.utc
        )

        managed = ManagedSession(

            session_id=session_id,

            user_id=user_id,

            created_at=now,

            last_activity=now,

            active=True,

            metadata=metadata or {}
        )

        self._sessions[
            session_id
        ] = managed

        return managed

    # ============================================================
    # GET SESSION
    # ============================================================

    def get(
        self,
        session_id: str
    ) -> Optional[ManagedSession]:
        """
        Retrieve a session.

        Returns None if it does not exist.
        """

        return self._sessions.get(
            session_id
        )

    # ============================================================
    # REQUIRE SESSION
    # ============================================================

    def require(
        self,
        session_id: str
    ) -> ManagedSession:
        """
        Retrieve a session or raise KeyError.
        """

        managed = self.get(
            session_id
        )

        if managed is None:

            raise KeyError(
                f"Unknown session: {session_id}"
            )

        return managed

    # ============================================================
    # VALIDATE SESSION
    # ============================================================

    def validate(
        self,
        session_id: str
    ) -> bool:
        """
        Check whether a session is currently valid.

        Validation checks:

            1. Session exists
            2. Session is active
            3. Session has not timed out
        """

        managed = self.get(
            session_id
        )

        if managed is None:

            return False

        if not managed.active:

            return False

        if self._is_expired(
            managed
        ):

            self.terminate(
                session_id,
                reason="Session timeout"
            )

            return False

        return True

    # ============================================================
    # TOUCH / REFRESH
    # ============================================================

    def touch(
        self,
        session_id: str
    ) -> ManagedSession:
        """
        Update the last activity time.

        This should be called when a valid request or
        security event occurs.
        """

        managed = self.require(
            session_id
        )

        if not managed.active:

            raise RuntimeError(
                "Cannot touch an inactive session"
            )

        if self._is_expired(
            managed
        ):

            self.terminate(
                session_id,
                reason="Session timeout"
            )

            raise RuntimeError(
                "Session has expired"
            )

        managed.last_activity = (
            datetime.now(
                timezone.utc
            )
        )

        return managed

    # ============================================================
    # TERMINATE SESSION
    # ============================================================

    def terminate(
        self,
        session_id: str,
        reason: str = "Security policy"
    ) -> bool:
        """
        Terminate a session.

        Returns:

            True  -> session was terminated
            False -> session did not exist
        """

        managed = self.get(
            session_id
        )

        if managed is None:

            return False

        managed.active = False

        managed.termination_reason = (
            reason
        )

        managed.last_activity = (
            datetime.now(
                timezone.utc
            )
        )

        return True

    # ============================================================
    # DELETE SESSION
    # ============================================================

    def remove(
        self,
        session_id: str
    ) -> bool:
        """
        Permanently remove a session from memory.

        This is different from terminate():

            terminate()
                keeps an audit state

            remove()
                removes the session object
        """

        if session_id not in self._sessions:

            return False

        del self._sessions[
            session_id
        ]

        return True

    # ============================================================
    # SESSION AGE
    # ============================================================

    def age_seconds(
        self,
        session_id: str
    ) -> float:
        """
        Return the total age of a session in seconds.
        """

        managed = self.require(
            session_id
        )

        now = datetime.now(
            timezone.utc
        )

        return max(
            0.0,
            (
                now -
                managed.created_at
            ).total_seconds()
        )

    # ============================================================
    # IDLE TIME
    # ============================================================

    def idle_seconds(
        self,
        session_id: str
    ) -> float:
        """
        Return the time since the last activity.
        """

        managed = self.require(
            session_id
        )

        now = datetime.now(
            timezone.utc
        )

        return max(
            0.0,
            (
                now -
                managed.last_activity
            ).total_seconds()
        )

    # ============================================================
    # EXPIRATION
    # ============================================================

    def _is_expired(
        self,
        managed: ManagedSession
    ) -> bool:
        """
        Check whether a session exceeded the inactivity timeout.
        """

        if not managed.active:

            return True

        now = datetime.now(
            timezone.utc
        )

        idle = (
            now -
            managed.last_activity
        ).total_seconds()

        return idle > self.timeout_seconds

    # ============================================================
    # UPDATE METADATA
    # ============================================================

    def update_metadata(
        self,
        session_id: str,
        values: Dict
    ) -> ManagedSession:
        """
        Add or update session metadata.

        Example:

            manager.update_metadata(
                session_id,
                {
                    "ip": "127.0.0.1",
                    "device": "desktop"
                }
            )
        """

        managed = self.require(
            session_id
        )

        if not managed.active:

            raise RuntimeError(
                "Cannot update inactive session"
            )

        if values:

            managed.metadata.update(
                values
            )

        self.touch(
            session_id
        )

        return managed

    # ============================================================
    # ACTIVE SESSIONS
    # ============================================================

    def active_sessions(
        self
    ):
        """
        Return all currently active sessions.
        """

        return [

            session

            for session
            in self._sessions.values()

            if session.active
            and
            not self._is_expired(
                session
            )
        ]

    # ============================================================
    # CLEANUP
    # ============================================================

    def cleanup_expired(
        self
    ) -> int:
        """
        Terminate all sessions that have exceeded
        the inactivity timeout.

        Returns the number of sessions terminated.
        """

        count = 0

        for session_id, managed in list(
            self._sessions.items()
        ):

            if (
                managed.active
                and
                self._is_expired(
                    managed
                )
            ):

                self.terminate(
                    session_id,
                    reason="Session timeout"
                )

                count += 1

        return count

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
        session_id: str
    ) -> Dict:
        """
        Return a serializable session status.
        """

        managed = self.require(
            session_id
        )

        return {

            "session_id":
                managed.session_id,

            "user_id":
                managed.user_id,

            "active":
                managed.active,

            "created_at":
                managed.created_at.isoformat(),

            "last_activity":
                managed.last_activity.isoformat(),

            "age_seconds":
                round(
                    self.age_seconds(
                        session_id
                    ),
                    2
                ),

            "idle_seconds":
                round(
                    self.idle_seconds(
                        session_id
                    ),
                    2
                ),

            "termination_reason":
                managed.termination_reason,

            "metadata":
                dict(
                    managed.metadata
                )
        }

    # ============================================================
    # COUNT
    # ============================================================

    def count(
        self
    ) -> int:
        """
        Return total number of managed sessions.
        """

        return len(
            self._sessions
        )

    def active_count(
        self
    ) -> int:
        """
        Return number of active sessions.
        """

        return len(
            self.active_sessions()
        )