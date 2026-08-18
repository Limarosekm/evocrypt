from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .agent import AdaptivePolicyAgent
from .state import SecurityState


@dataclass(frozen=True)
class SecurityDecision:
    """
    Immutable result of an EvoCrypt RL policy decision.
    """

    action: str
    trust_score: float
    state: str

    q_values: Dict[str, float]

    confidence: float

    risk_level: str

    reasons: list[str] = field(
        default_factory=list
    )

    features: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "trust_score": self.trust_score,
            "state": self.state,
            "q_values": dict(self.q_values),
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "reasons": list(self.reasons),
            "features": dict(self.features),
        }


class AdaptiveSecurityPolicy:
    """
    Production inference layer for EvoCrypt RL.

    Responsibilities:

        1. Load a trained RL policy.
        2. Convert security features into an RL state.
        3. Select the learned action.
        4. Apply EvoCrypt safety boundaries.
        5. Return an explainable decision.

    This class deliberately does NOT:

        - access PostgreSQL
        - access Flask
        - modify sessions
        - generate cryptographic keys
        - execute cryptographic operations

    It only makes a security-policy decision.
    """

    VERSION = "1.0"

    ACTIONS = (
        "NORMAL",
        "MONITOR",
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    )

    def __init__(
        self,
        agent: AdaptivePolicyAgent,
    ):
        self.agent = agent

    # ============================================================
    # LOAD POLICY
    # ============================================================

    @classmethod
    def from_file(
        cls,
        path: str | Path,
    ) -> "AdaptiveSecurityPolicy":

        agent = AdaptivePolicyAgent()

        agent.load(
            str(path)
        )

        return cls(
            agent
        )

    # ============================================================
    # DECISION
    # ============================================================

    def decide(
        self,
        *,
        trust_score: float,
        threat_score: Optional[float] = None,
        behavioral_risk: int = 0,
        device_risk: int = 0,
        transaction_risk: int = 0,
        recovery_phase: int = 0,
        previous_action: str = "NONE",
        stability_steps: int = 0,
        reasons: Optional[list[str]] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> SecurityDecision:

        trust_score = self._clamp(
            trust_score
        )

        threat_score = self._clamp(
            (
                threat_score
                if threat_score is not None
                else 100.0 - trust_score
            )
        )

        behavioral_risk = self._risk_bucket(
            behavioral_risk
        )

        device_risk = self._risk_bucket(
            device_risk
        )

        transaction_risk = self._risk_bucket(
            transaction_risk
        )

        recovery_phase = max(
            0,
            min(
                2,
                int(recovery_phase)
            )
        )

        stability_steps = max(
            0,
            min(
                9,
                int(stability_steps)
            )
        )

        previous_action = (
            str(previous_action)
            .upper()
            .strip()
        )

        # --------------------------------------------------------
        # Build the same state representation used by training.
        # --------------------------------------------------------
        state = self._build_state(
            trust_score=trust_score,
            threat_score=threat_score,
            behavioral_risk=behavioral_risk,
            device_risk=device_risk,
            transaction_risk=transaction_risk,
            recovery_phase=recovery_phase,
            previous_action=previous_action,
            stability_steps=stability_steps,
        )

        # --------------------------------------------------------
        # Learned policy
        # --------------------------------------------------------

        learned_action = self.agent.choose_action(
            state,
            explore=False
        )

        # --------------------------------------------------------
        # Mandatory EvoCrypt safety boundary
        # --------------------------------------------------------

        safe_action = self.agent.safe_action(
            trust_score,
            learned_action
        )

        # --------------------------------------------------------
        # Q-values
        # --------------------------------------------------------

        q_values = self._get_q_values(
            state
        )

        confidence = self._confidence(
            q_values,
            learned_action
        )

        risk_level = self._risk_level(
            trust_score
        )

        decision_reasons = list(
            reasons or []
        )

        decision_reasons.extend(
            self._decision_reasons(
                trust_score=trust_score,
                threat_score=threat_score,
                learned_action=learned_action,
                safe_action=safe_action,
                behavioral_risk=behavioral_risk,
                device_risk=device_risk,
                transaction_risk=transaction_risk,
            )
        )

        features = {
            "threat_score": threat_score,
            "behavioral_risk": behavioral_risk,
            "device_risk": device_risk,
            "transaction_risk": transaction_risk,
            "recovery_phase": recovery_phase,
            "previous_action": previous_action,
            "stability_steps": stability_steps,
        }

        if context:
            features.update(
                dict(context)
            )

        return SecurityDecision(
            action=safe_action,
            trust_score=trust_score,
            state=state,
            q_values=q_values,
            confidence=confidence,
            risk_level=risk_level,
            reasons=decision_reasons,
            features=features,
        )

    # ============================================================
    # STATE BUILDING
    # ============================================================

    def _build_state(
        self,
        *,
        trust_score: float,
        threat_score: float,
        behavioral_risk: int,
        device_risk: int,
        transaction_risk: int,
        recovery_phase: int,
        previous_action: str,
        stability_steps: int,
    ) -> str:

        state = SecurityState.from_observation(
            trust_score=trust_score,
            threat_score=threat_score,
            behavioral_risk=behavioral_risk,
            contextual_risk=device_risk,
            transaction_risk=(
                transaction_risk * 33.333
            ),
            recovery_phase=recovery_phase,
            previous_action=previous_action,
            stability_steps=stability_steps,
            pqc_enabled=(
                previous_action == "HYBRID_PQC"
            ),
        )

        return state.encode()
    # ============================================================
    # Q VALUES
    # ============================================================

    def _get_q_values(
        self,
        state: str,
    ) -> Dict[str, float]:

        table = getattr(
            self.agent,
            "q_table",
            {}
        )

        values = table.get(
            state
        )

        if values is None:

            # Compatibility with older policies.
            fallback = (
                self.agent.state_from_trust(
                    100
                )
            )

            values = table.get(
                fallback,
                {
                    action: 0.0
                    for action in self.ACTIONS
                }
            )

        return {
            action: round(
                float(
                    values.get(
                        action,
                        0.0
                    )
                ),
                4
            )
            for action in self.ACTIONS
        }

    # ============================================================
    # CONFIDENCE
    # ============================================================

    @staticmethod
    def _confidence(
        q_values: Dict[str, float],
        selected_action: str,
    ) -> float:

        values = sorted(
            q_values.values(),
            reverse=True
        )

        if not values:
            return 0.0

        best = values[0]

        second = (
            values[1]
            if len(values) > 1
            else 0.0
        )

        scale = max(
            1.0,
            abs(best)
        )

        margin = (
            best - second
        ) / scale

        confidence = (
            0.5
            +
            0.5 * margin
        )

        return round(
            max(
                0.0,
                min(
                    1.0,
                    confidence
                )
            ),
            4
        )

    # ============================================================
    # EXPLANATION
    # ============================================================

    @staticmethod
    def _decision_reasons(
        *,
        trust_score: float,
        threat_score: float,
        learned_action: str,
        safe_action: str,
        behavioral_risk: int,
        device_risk: int,
        transaction_risk: int,
    ) -> list[str]:

        reasons = []

        if threat_score >= 70:
            reasons.append(
                "High estimated threat level"
            )

        elif threat_score >= 40:
            reasons.append(
                "Elevated estimated threat level"
            )

        if behavioral_risk >= 2:
            reasons.append(
                "Behavioral anomaly detected"
            )

        if device_risk >= 2:
            reasons.append(
                "Elevated device risk"
            )

        if transaction_risk >= 2:
            reasons.append(
                "Elevated transaction risk"
            )

        if trust_score < 20:
            reasons.append(
                "Critical trust level"
            )

        elif trust_score < 40:
            reasons.append(
                "High-risk trust level"
            )

        if learned_action != safe_action:
            reasons.append(
                "Safety policy overrode the learned action"
            )

        if not reasons:
            reasons.append(
                "Security state remains within "
                "the learned operating region"
            )

        return reasons

    # ============================================================
    # RISK
    # ============================================================

    @staticmethod
    def _risk_level(
        trust_score: float,
    ) -> str:

        if trust_score >= 70:
            return "LOW"

        if trust_score >= 40:
            return "MEDIUM"

        if trust_score >= 20:
            return "HIGH"

        return "CRITICAL"

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _bucket(
        value: float,
    ) -> int:

        value = max(
            0.0,
            min(
                100.0,
                float(value)
            )
        )

        return min(
            9,
            int(value // 10)
        )

    @staticmethod
    def _risk_bucket(
        value: Any,
    ) -> int:

        try:
            value = int(value)
        except (
            TypeError,
            ValueError,
        ):
            value = 0

        return max(
            0,
            min(
                3,
                value
            )
        )

    @staticmethod
    def _clamp(
        value: Any,
    ) -> float:

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            value = 0.0

        return max(
            0.0,
            min(
                100.0,
                value
            )
        )