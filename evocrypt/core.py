from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import EvoCryptConfig
from .trust.scorer import TrustScorer
from .rl.agent import AdaptivePolicyAgent
from .crypto.key_manager import KeyManager
from .session.manager import SessionManager


@dataclass
class EvoSession:
    """
    Represents one active EvoCrypt-protected user session.
    """

    session_id: str
    user_id: str

    # Current continuous trust score
    trust_score: float

    # Security action selected by the policy engine
    action: str = "MONITOR"

    # Cryptographic protection currently assigned
    crypto_mode: str = "AES-256-GCM"

    # Current risk classification
    risk_level: str = "LOW"

    # Whether the session is still valid
    active: bool = True

    # Session creation time
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Time of the latest security decision
    last_decision_at: Optional[datetime] = None

    # Explanation for the latest security decision
    reasons: list = field(default_factory=list)


class EvoCrypt:
    """
    Main public API of the EvoCrypt framework.

    EvoCrypt integrates:

        Behavioral Trust
              ↓
        Trust Evaluation
              ↓
        RL Policy Engine
              ↓
        Adaptive Security Action
              ↓
        Key / Crypto Management
              ↓
        Session Protection
    """

    def __init__(
        self,
        config: Optional[EvoCryptConfig] = None,
        **kwargs
    ):
        """
        Create a new EvoCrypt security engine.

        Example:

            security = EvoCrypt()

        Or:

            security = EvoCrypt(
                adaptive=True,
                pqc_enabled=True,
                initial_trust=90
            )
        """

        # ---------------------------------------------------------
        # Configuration
        # ---------------------------------------------------------

        self.config = config or EvoCryptConfig(**kwargs)

        # ---------------------------------------------------------
        # Trust Engine
        # ---------------------------------------------------------

        self.trust = TrustScorer(
            self.config.low_trust_threshold,
            self.config.critical_trust_threshold
        )

        # ---------------------------------------------------------
        # Reinforcement Learning Policy Engine
        # ---------------------------------------------------------

        self.agent = AdaptivePolicyAgent()

        # ---------------------------------------------------------
        # Cryptographic Key Manager
        # ---------------------------------------------------------

        self.keys = KeyManager(
            self.config.key_rotation_seconds
        )

        # ---------------------------------------------------------
        # Session Manager
        # ---------------------------------------------------------

        self.sessions = SessionManager()

        # ---------------------------------------------------------
        # Active EvoCrypt sessions
        # ---------------------------------------------------------

        self._sessions: Dict[str, EvoSession] = {}

    # =============================================================
    # SESSION MANAGEMENT
    # =============================================================

    def start_session(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Start a new EvoCrypt-protected session.

        Steps:

        1. Create EvoCrypt session
        2. Assign initial trust score
        3. Register session
        4. Generate session encryption key
        5. Return current security status
        """

        session = EvoSession(
            session_id=session_id,
            user_id=user_id,
            trust_score=self.config.initial_trust
        )

        self._sessions[session_id] = session

        # Register session with SessionManager
        self.sessions.create(
            session_id,
            user_id
        )

        # Generate first session key
        self.keys.create_key(
            session_id
        )

        return self.get_status(
            session_id
        )

    # =============================================================
    # CONTINUOUS BEHAVIOR EVALUATION
    # =============================================================

    def record_behavior(
        self,
        session_id: str,
        signals: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a new behavioral observation.

        Example signals:

            {
                "typing_speed": 5.2,
                "avg_key_hold": 110,
                "mouse_speed": 220,
                "mouse_distance": 950,
                "click_count": 12,
                "scroll_distance": 300,
                "idle_time": 2
            }

        Context can contain:

            {
                "ip_changed": False,
                "device_changed": False,
                "unusual_time": False,
                "suspicious": False
            }
        """

        session = self._require(
            session_id
        )

        # Do nothing if the session has already been terminated
        if not session.active:
            return self.get_status(
                session_id
            )

        # ---------------------------------------------------------
        # STEP 1: Trust Evaluation
        # ---------------------------------------------------------

        result = self.trust.evaluate(
            signals=signals,
            previous_score=session.trust_score,
            context=context or {}
        )

        # Update continuous trust score
        session.trust_score = result["score"]

        # ---------------------------------------------------------
        # STEP 2: Convert Trust Score → RL State
        # ---------------------------------------------------------

        state = self.agent.state_from_trust(
            session.trust_score
        )

        # ---------------------------------------------------------
        # STEP 3: RL Policy Selection
        # ---------------------------------------------------------

        action = self.agent.choose_action(
            state,
            explore=False
        )

        # ---------------------------------------------------------
        # STEP 4: Apply Security Action
        # ---------------------------------------------------------

        session.reasons = result["reasons"]

        session.last_decision_at = (
            datetime.now(timezone.utc)
        )

        return self._apply(
            session,
            action
        )

    # =============================================================
    # EXTERNAL RISK EVENTS
    # =============================================================

    def apply_external_risk(
        self,
        session_id: str,
        delta: float,
        reason: str
    ) -> Dict[str, Any]:
        """
        Apply a security risk event that does not directly
        come from behavioral signals.

        Example:

            security.apply_external_risk(
                session_id,
                -20,
                "Suspicious transaction"
            )
        """

        session = self._require(
            session_id
        )

        # Update trust score
        session.trust_score = max(
            0,
            min(
                100,
                session.trust_score + delta
            )
        )

        # Store explanation
        session.reasons = [
            reason
        ]

        # Convert score into RL state
        state = self.agent.state_from_trust(
            session.trust_score
        )

        # Select adaptive security action
        action = self.agent.choose_action(
            state,
            explore=False
        )

        session.last_decision_at = (
            datetime.now(timezone.utc)
        )

        return self._apply(
            session,
            action
        )

    # =============================================================
    # APPLY SECURITY POLICY
    # =============================================================

    def _apply(
        self,
        session: EvoSession,
        action: str
    ) -> Dict[str, Any]:
        """
        Apply the security action selected by the RL engine.
        """

        session.action = action

        # ---------------------------------------------------------
        # NORMAL
        # ---------------------------------------------------------

        if action == "NORMAL":

            session.crypto_mode = (
                "AES-256-GCM"
            )

        # ---------------------------------------------------------
        # MONITOR
        # ---------------------------------------------------------

        elif action == "MONITOR":

            session.crypto_mode = (
                "AES-256-GCM"
            )

        # ---------------------------------------------------------
        # ROTATE KEY
        # ---------------------------------------------------------

        elif action == "ROTATE_KEY":

            self.keys.rotate(
                session.session_id
            )

            session.crypto_mode = (
                "AES-256-GCM"
            )

        # ---------------------------------------------------------
        # REAUTHENTICATE
        # ---------------------------------------------------------

        elif action == "REAUTHENTICATE":

            # Rotate the current session key
            self.keys.rotate(
                session.session_id
            )

            session.crypto_mode = (
                "AES-256-GCM"
            )

        # ---------------------------------------------------------
        # HYBRID PQC
        # ---------------------------------------------------------

        elif action == "HYBRID_PQC":

            # A high-risk state triggers key rotation
            self.keys.rotate(
                session.session_id
            )

            if self.config.pqc_enabled:

                session.crypto_mode = (
                    "HYBRID-PQC"
                )

            else:

                # Important:
                # Do not falsely claim that classical
                # cryptography is post-quantum.
                session.crypto_mode = (
                    "PQC-READY"
                )

        # ---------------------------------------------------------
        # TERMINATE SESSION
        # ---------------------------------------------------------

        elif action == "TERMINATE_SESSION":

            session.crypto_mode = (
                "BLOCKED"
            )

            if self.config.allow_session_termination:

                session.active = False

                self.sessions.terminate(
                    session.session_id
                )

        # ---------------------------------------------------------
        # Calculate risk classification
        # ---------------------------------------------------------

        session.risk_level = self._risk(
            session.trust_score
        )

        return self.get_status(
            session.session_id
        )

    # =============================================================
    # RISK CLASSIFICATION
    # =============================================================

    @staticmethod
    def _risk(
        score: float
    ) -> str:
        """
        Convert numerical trust score into a risk level.
        """

        if score >= 70:
            return "LOW"

        if score >= 40:
            return "MEDIUM"

        if score >= 20:
            return "HIGH"

        return "CRITICAL"

    # =============================================================
    # GET SECURITY STATUS
    # =============================================================

    def get_status(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Return the complete current security state
        of a session.
        """

        session = self._require(
            session_id
        )

        key_status = self.keys.status(
            session_id
        )

        return {

            # Session information
            "session_id":
                session.session_id,

            "user_id":
                session.user_id,

            "active":
                session.active,

            # Trust information
            "trust_score":
                round(
                    session.trust_score,
                    1
                ),

            "risk_level":
                session.risk_level,

            # RL decision
            "action":
                session.action,

            # Cryptographic protection
            "crypto_mode":
                session.crypto_mode,

            # Key information
            "key_version":
                key_status["version"],

            "key_age_seconds":
                key_status["age_seconds"],

            "key_rotation_count":
                key_status["rotation_count"],

            # Explainability
            "reasons":
                session.reasons
        }

    # =============================================================
    # RL TRAINING
    # =============================================================

    def train_step(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str
    ):
        """
        Perform one Q-learning update.

        Example:

            security.train_step(
                "MEDIUM",
                "ROTATE_KEY",
                5,
                "HIGH"
            )

        Training can be performed offline so that runtime
        inference remains lightweight.
        """

        self.agent.update(
            state,
            action,
            reward,
            next_state
        )

    # =============================================================
    # INTERNAL SESSION LOOKUP
    # =============================================================

    def _require(
        self,
        session_id: str
    ) -> EvoSession:
        """
        Return a registered EvoCrypt session.

        Raises:
            KeyError: if the session does not exist.
        """

        if session_id not in self._sessions:

            raise KeyError(
                f"Unknown EvoCrypt session: {session_id}"
            )

        return self._sessions[
            session_id
        ]