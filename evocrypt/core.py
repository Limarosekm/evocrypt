
import time

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import EvoCryptConfig
from .trust.scorer import TrustScorer
from .rl.agent import AdaptivePolicyAgent
from .crypto.key_manager import KeyManager
from .crypto.engine import AdaptiveCryptoEngine
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
        Adaptive Crypto Policy
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

        self.keys = KeyManager()

        # ---------------------------------------------------------
        # Adaptive Cryptographic Engine
        # ---------------------------------------------------------

        self.crypto = AdaptiveCryptoEngine(
            key_manager=self.keys,
            pqc_enabled=self.config.pqc_enabled
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
        """

        session = EvoSession(
            session_id=session_id,
            user_id=user_id,
            trust_score=self.config.initial_trust
        )

        self._sessions[session_id] = session

        # Register session
        self.sessions.create(
            session_id,
            user_id
        )

        # Generate first session key
        self.keys.generate_key(
            session_id
        )

        # Initialize adaptive crypto policy
        self.crypto.initialize_session(
            session_id=session_id,
            trust_score=session.trust_score,
            action="NORMAL"
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
        """

        session = self._require(
            session_id
        )

        # Do nothing if session has been terminated
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

        session.trust_score = result["score"]

        # ---------------------------------------------------------
        # STEP 2: Trust Score → RL State
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

        # Apply mandatory safety boundaries
        action = self.agent.safe_action(
            session.trust_score,
            action
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
        Apply an external security risk event.
        """

        session = self._require(
            session_id
        )

        if not session.active:
            return self.get_status(
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

        # Select security action
        action = self.agent.choose_action(
            state,
            explore=False
        )

        # Apply safety boundaries
        action = self.agent.safe_action(
            session.trust_score,
            action
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
        Apply the RL-selected security action and update
        adaptive cryptographic protection.
        """

        session.action = action

        session.last_decision_at = (
            datetime.now(timezone.utc)
        )

        # ---------------------------------------------------------
        # Adaptive Cryptographic Policy
        # ---------------------------------------------------------

        crypto_result = self.crypto.update(
            session_id=session.session_id,
            trust_score=session.trust_score,
            action=action
        )

        policy = crypto_result["policy"]

        # ---------------------------------------------------------
        # TERMINATE SESSION
        # ---------------------------------------------------------

        if action == "TERMINATE_SESSION":

            session.crypto_mode = "BLOCKED"

            if self.config.allow_session_termination:

                session.active = False

                self.sessions.terminate(
                    session.session_id
                )

                self.crypto.remove_session(
                    session.session_id
                )

        # ---------------------------------------------------------
        # OTHER SECURITY LEVELS
        # ---------------------------------------------------------

        else:

            session.crypto_mode = policy.mode

        # ---------------------------------------------------------
        # Risk Classification
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

        # Get current key directly from KeyManager
        key_record = self.keys.get_key(
            session_id
        )

        # Get current adaptive crypto policy
        crypto_status = self.crypto.status(
            session_id
        )

        # ---------------------------------------------------------
        # Key information
        # ---------------------------------------------------------

        if key_record is None:

            key_version = 0
            key_age_seconds = 0
            key_rotation_count = 0

        else:

            key_version = key_record.get(
                "version",
                0
            )

            key_age_seconds = max(
                0,
                int(
                    time.time()
                    - key_record["created_at"]
                )
            )

            key_rotation_count = max(
                0,
                key_version - 1
            )

        # ---------------------------------------------------------
        # Return complete security status
        # ---------------------------------------------------------

        return {

            # Session
            "session_id":
                session.session_id,

            "user_id":
                session.user_id,

            "active":
                session.active,

            # Trust
            "trust_score":
                round(
                    session.trust_score,
                    1
                ),

            "risk_level":
                session.risk_level,

            # RL
            "action":
                session.action,

            # Crypto
            "crypto_mode":
                session.crypto_mode,

            "cipher":
                crypto_status.get(
                    "cipher",
                    "NONE"
                ),

            "key_exchange":
                crypto_status.get(
                    "key_exchange",
                    "NONE"
                ),

            "pqc_enabled":
                crypto_status.get(
                    "pqc_enabled",
                    False
                ),

            "crypto_rotation_interval":
                crypto_status.get(
                    "rotation_interval",
                    0
                ),

            # Key
            "key_version":
                key_version,

            "key_age_seconds":
                key_age_seconds,

            "key_rotation_count":
                key_rotation_count,

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
        """

        if session_id not in self._sessions:

            raise KeyError(
                f"Unknown EvoCrypt session: {session_id}"
            )

        return self._sessions[
            session_id
        ]

    # =============================================================
    # ATTACK SIMULATION
    # =============================================================

    def simulate_hijack(
        self,
        session_id: str,
        severity: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Inject realistic hijacking indicators through the real
        Trust → RL → Security pipeline.
        """

        session = self._require(
            session_id
        )

        if not session.active:
            return self.get_status(
                session_id
            )

        profiles = {

            "moderate": {

                "signals": {
                    "typing_speed": 0.2,
                    "avg_key_hold": 480,
                    "mouse_speed": 1900,
                    "mouse_distance": 4000,
                    "click_count": 2,
                    "scroll_distance": 0,
                    "idle_time": 0,
                },

                "context": {
                    "device_changed": True,
                    "ip_changed": False,
                    "unusual_time": False,
                },
            },

            "high": {

                "signals": {
                    "typing_speed": 0.1,
                    "avg_key_hold": 490,
                    "mouse_speed": 2000,
                    "mouse_distance": 16000,
                    "click_count": 0,
                    "scroll_distance": 0,
                    "idle_time": 0,
                    "suspicious": True,
                },

                "context": {
                    "device_changed": True,
                    "ip_changed": True,
                    "unusual_time": True,
                },
            },
        }

        profile = profiles.get(
            severity,
            profiles["moderate"]
        )

        status = self.record_behavior(
            session_id,
            signals=profile["signals"],
            context=profile["context"]
        )

        if severity == "high" and status["active"]:

            status = self.apply_external_risk(
                session_id,
                -15,
                "Session token reused from an unrecognized device/network"
            )

        return status

