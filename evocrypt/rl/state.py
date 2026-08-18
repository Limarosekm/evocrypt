from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _flag(value: Any) -> int:
    return 1 if bool(value) else 0


def _bucket(value: float, edges) -> int:
    for index, edge in enumerate(edges):
        if value <= edge:
            return index
    return len(edges)


@dataclass(frozen=True)
class SecurityState:
    """
    Canonical EvoCrypt RL state.

    This is the single state representation shared by:

        training
        evaluation
        policy inference
        EvoCrypt core
        demo integration

    All components must use encode() rather than constructing
    state strings manually.
    """

    trust_bucket: int
    threat_bucket: int
    trust_delta_bucket: int

    behavioral_risk: int
    contextual_risk: int
    transaction_risk: int

    key_age_bucket: int

    recovery_phase: int
    stability_steps: int
    previous_action: str
    pqc_enabled: int

    VERSION = 3

    ACTIONS = (
        "NORMAL",
        "MONITOR",
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    )

    @classmethod
    def from_observation(
        cls,
        *,
        trust_score: float,
        threat_score: float = 0.0,
        previous_trust_score: Optional[float] = None,
        trust_penalty: float = 0.0,
        signals: Optional[Mapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
        behavioral_risk: Optional[int] = None,
        contextual_risk: Optional[int] = None,
        transaction_risk: float = 0.0,
        key_age_seconds: float = 0.0,
        key_rotation_seconds: float = 900.0,
        recovery_phase: int = 0,
        previous_action: str = "MONITOR",
        stability_steps: int = 0,
        pqc_enabled: bool = False,
            ) -> "SecurityState":

        signals = signals or {}
        context = context or {}

        # --------------------------------------------------------
        # Trust
        # --------------------------------------------------------

        trust = max(
            0.0,
            min(
                100.0,
                _number(trust_score),
            ),
        )

        threat = max(
            0.0,
            min(
                100.0,
                _number(threat_score),
            ),
        )

        # --------------------------------------------------------
        # Trust trend
        # --------------------------------------------------------

        if previous_trust_score is None:
            delta = -max(
                0.0,
                _number(trust_penalty),
            )
        else:
            delta = (
                trust
                - _number(previous_trust_score)
            )

        if delta >= 3:
            delta_bucket = 0
        elif delta >= -3:
            delta_bucket = 1
        elif delta >= -10:
            delta_bucket = 2
        else:
            delta_bucket = 3

        # --------------------------------------------------------
        # Behavioral risk
        # --------------------------------------------------------

        if behavioral_risk is not None:

            behavioral_bucket = max(
                0,
                min(
                    3,
                    int(behavioral_risk),
                ),
            )

        else:

            observed_behavior = any(
                key in signals
                and signals[key] is not None
                for key in (
                    "typing_speed",
                    "avg_key_hold",
                    "mouse_speed",
                    "mouse_distance",
                    "click_count",
                    "scroll_distance",
                    "idle_time",
                )
            )

            penalty = max(
                0.0,
                _number(trust_penalty),
            )

            if penalty >= 25:
                behavioral_bucket = 3
            elif penalty >= 12:
                behavioral_bucket = 2
            elif penalty > 0:
                behavioral_bucket = 1
            elif observed_behavior:
                behavioral_bucket = 0
            else:
                behavioral_bucket = 1

        # --------------------------------------------------------
        # Contextual risk
        # --------------------------------------------------------

        if contextual_risk is not None:

            contextual_bucket = max(
                0,
                min(
                    3,
                    int(contextual_risk),
                ),
            )

        else:

            context_count = sum(
                _flag(
                    context.get(key)
                )
                for key in (
                    "ip_changed",
                    "device_changed",
                    "location_changed",
                    "unusual_time",
                    "suspicious",
                )
            )

            contextual_bucket = min(
                3,
                context_count,
            )

        # --------------------------------------------------------
        # Transaction risk
        # --------------------------------------------------------

        tx = max(
            0.0,
            min(
                100.0,
                _number(transaction_risk),
            ),
        )

        if tx >= 75:
            transaction_bucket = 3
        elif tx >= 40:
            transaction_bucket = 2
        elif tx > 0:
            transaction_bucket = 1
        else:
            transaction_bucket = 0

        # --------------------------------------------------------
        # Key age
        # --------------------------------------------------------

        rotation = max(
            1.0,
            _number(
                key_rotation_seconds,
                900.0,
            ),
        )

        age_ratio = (
            max(
                0.0,
                _number(key_age_seconds),
            )
            / rotation
        )

        if age_ratio < 0.5:
            key_age_bucket = 0
        elif age_ratio < 1.0:
            key_age_bucket = 1
        elif age_ratio < 2.0:
            key_age_bucket = 2
        else:
            key_age_bucket = 3

        # --------------------------------------------------------
        # Previous action
        # --------------------------------------------------------

        action = (
            str(
                previous_action
                or "MONITOR"
            )
            .upper()
            .strip()
        )

        if action == "NONE":
            action = "MONITOR"

        if action not in cls.ACTIONS:
            action = "MONITOR"
                # --------------------------------------------------------
        # Recovery phase
        # --------------------------------------------------------

        recovery_phase = max(
            0,
            min(
                2,
                int(recovery_phase),
            ),
        )

        # --------------------------------------------------------
        # Stability steps
        # --------------------------------------------------------

        stability_steps = max(
            0,
            min(
                3,
                int(stability_steps),
            ),
        )

        return cls(
    trust_bucket=_bucket(
        trust,
        (19, 39, 69),
    ),

    threat_bucket=min(
        9,
        int(threat // 10),
    ),

    trust_delta_bucket=delta_bucket,

    behavioral_risk=behavioral_bucket,

    contextual_risk=contextual_bucket,

    transaction_risk=transaction_bucket,

    key_age_bucket=key_age_bucket,

    recovery_phase=max(
        0,
        min(2, int(recovery_phase)),
    ),

    stability_steps=max(
        0,
        min(9, int(stability_steps)),
    ),

    previous_action=action,

    pqc_enabled=_flag(
        pqc_enabled
    ),
)

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def encode(self) -> str:
        """
        Canonical serialized state.

        Format:

        v3|t|h|d|b|c|x|k|r|a|s|p
        """

        action_index = (
            self.ACTIONS.index(
                self.previous_action
            ) + 1
        )

        return (
            f"v{self.VERSION}"
            f"|t{self.trust_bucket}"
            f"|h{self.threat_bucket}"
            f"|d{self.trust_delta_bucket}"
            f"|b{self.behavioral_risk}"
            f"|c{self.contextual_risk}"
            f"|x{self.transaction_risk}"
            f"|k{self.key_age_bucket}"
            f"|r{self.recovery_phase}"
            f"|a{action_index}"
            f"|s{self.stability_steps}"
            f"|p{self.pqc_enabled}"
        )
    def to_dict(self) -> Dict[str, Any]:

        return {
            "version": self.VERSION,
            "trust_bucket": self.trust_bucket,
            "threat_bucket": self.threat_bucket,
            "trust_delta_bucket": self.trust_delta_bucket,
            "behavioral_risk": self.behavioral_risk,
            "contextual_risk": self.contextual_risk,
            "transaction_risk": self.transaction_risk,
            "key_age_bucket": self.key_age_bucket,
            "previous_action": self.previous_action,
            "recovery_phase": self.recovery_phase,
            "stability_steps": self.stability_steps,
            "pqc_enabled": bool(
                self.pqc_enabled
            ),
            "encoded": self.encode(),
        }