from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .reward import SecurityReward
from .state import SecurityState


ACTIONS = (
    "NORMAL",
    "MONITOR",
    "ROTATE_KEY",
    "REAUTHENTICATE",
    "HYBRID_PQC",
    "TERMINATE_SESSION",
)


@dataclass(frozen=True)
class Scenario:
    name: str
    initial_trust: float
    initial_threat: float
    behavioral_risk: int
    device_risk: int
    transaction_risk: int
    attack_persistence: float
    recovery_rate: float


SCENARIOS: Dict[str, Scenario] = {
    "normal": Scenario(
        name="normal",
        initial_trust=92.0,
        initial_threat=8.0,
        behavioral_risk=0,
        device_risk=0,
        transaction_risk=0,
        attack_persistence=0.0,
        recovery_rate=5.0,
    ),

    "behavioral_anomaly": Scenario(
        name="behavioral_anomaly",
        initial_trust=72.0,
        initial_threat=38.0,
        behavioral_risk=3,
        device_risk=0,
        transaction_risk=0,
        attack_persistence=0.35,
        recovery_rate=4.0,
    ),

    "device_takeover": Scenario(
        name="device_takeover",
        initial_trust=58.0,
        initial_threat=68.0,
        behavioral_risk=2,
        device_risk=3,
        transaction_risk=0,
        attack_persistence=0.70,
        recovery_rate=3.0,
    ),

    "high_value_transaction": Scenario(
        name="high_value_transaction",
        initial_trust=64.0,
        initial_threat=52.0,
        behavioral_risk=0,
        device_risk=0,
        transaction_risk=3,
        attack_persistence=0.45,
        recovery_rate=4.0,
    ),

    "combined_attack": Scenario(
        name="combined_attack",
        initial_trust=42.0,
        initial_threat=88.0,
        behavioral_risk=3,
        device_risk=3,
        transaction_risk=3,
        attack_persistence=0.90,
        recovery_rate=2.0,
    ),
}


@dataclass
class EnvironmentState:
    trust: float
    previous_trust: float
    threat: float
    previous_threat: float
    behavioral_risk: int
    device_risk: int
    transaction_risk: int
    previous_action: str
    recovery_phase: int
    step_count: int


class EvoCryptEnvironment:
    """
    Stateful security-control environment for EvoCrypt.

    The environment models:

        - persistent threats
        - trust degradation/recovery
        - behavioral anomalies
        - device compromise
        - transaction risk
        - action costs
        - security recovery

    Cryptographic primitives are intentionally outside the
    environment. The RL layer selects a security action;
    EvoCrypt core applies that action.
    """

    MAX_STEPS = 12

    ACTION_THREAT_EFFECT = {
        "NORMAL": 0.0,
        "MONITOR": -5.0,
        "ROTATE_KEY": -14.0,
        "REAUTHENTICATE": -24.0,
        "HYBRID_PQC": -28.0,
        "TERMINATE_SESSION": -100.0,
    }

    ACTION_TRUST_EFFECT = {
        "NORMAL": 1.5,
        "MONITOR": 1.0,
        "ROTATE_KEY": 0.5,
        "REAUTHENTICATE": 2.5,
        "HYBRID_PQC": 1.5,
        "TERMINATE_SESSION": 0.0,
    }

    def __init__(
        self,
        seed: Optional[int] = 42,
    ):
        self.random = random.Random(seed)

        self.scenario: Optional[Scenario] = None
        self.state: Optional[EnvironmentState] = None

        self.trust_score = 0.0
        self.threat = 0.0

    # ============================================================
    # RESET
    # ============================================================

    def reset(
        self,
        scenario_name: str = "normal",
    ) -> str:

        if scenario_name not in SCENARIOS:
            raise ValueError(
                f"Unknown scenario: {scenario_name}"
            )

        self.scenario = SCENARIOS[
            scenario_name
        ]

        initial_trust = self._clamp(
            self.scenario.initial_trust
        )

        initial_threat = self._clamp(
            self.scenario.initial_threat
        )

        self.state = EnvironmentState(
            trust=initial_trust,
            previous_trust=initial_trust,
            threat=initial_threat,
            previous_threat=initial_threat,
            behavioral_risk=self.scenario.behavioral_risk,
            device_risk=self.scenario.device_risk,
            transaction_risk=self.scenario.transaction_risk,
            previous_action="MONITOR",
            recovery_phase=0,
            step_count=0,
        )

        self.trust_score = self.state.trust
        self.threat = self.state.threat

        return self._encode_state()

    # ============================================================
    # STEP
    # ============================================================

    def step(
        self,
        action: str,
    ) -> Tuple[str, float, bool, dict]:

        if self.state is None:
            raise RuntimeError(
                "Environment must be reset before step()."
            )

        if action not in ACTIONS:
            raise ValueError(
                f"Unknown action: {action}"
            )

        previous_threat = self.state.threat
        previous_trust = self.state.trust
        previous_action = self.state.previous_action

        self.state.step_count += 1

        # --------------------------------------------------------
        # Threat dynamics
        # --------------------------------------------------------

        action_effect = self.ACTION_THREAT_EFFECT[
            action
        ]

        persistence_pressure = (
            self.scenario.attack_persistence
            * max(
                0.0,
                self.state.threat,
            )
            * 0.08
        )

        threat_delta = (
            action_effect
            + persistence_pressure
        )

        if self.state.threat <= 15.0:
            threat_delta -= self.scenario.recovery_rate

        if (
            action == "NORMAL"
            and self.state.threat >= 40.0
        ):
            threat_delta += 8.0

        self.state.threat = self._clamp(
            self.state.threat + threat_delta
        )

        # --------------------------------------------------------
        # Trust dynamics
        # --------------------------------------------------------

        threat_pressure = (
            self.state.threat - 25.0
        ) * 0.10

        trust_delta = (
            self.ACTION_TRUST_EFFECT[action]
            - max(
                0.0,
                threat_pressure,
            )
        )

        if self.state.threat <= 15.0:
            trust_delta += self.scenario.recovery_rate

        self.state.trust = self._clamp(
            self.state.trust + trust_delta
        )

        # --------------------------------------------------------
        # Recovery phase
        # --------------------------------------------------------

        if self.state.threat >= 70:
            self.state.recovery_phase = 0

        elif self.state.threat >= 30:
            self.state.recovery_phase = 1

        else:
            self.state.recovery_phase = 2

        # --------------------------------------------------------
        # Preserve previous values
        # --------------------------------------------------------

        self.state.previous_trust = previous_trust
        self.state.previous_threat = previous_threat
        self.state.previous_action = action

        self.trust_score = self.state.trust
        self.threat = self.state.threat

        # --------------------------------------------------------
        # Terminal conditions
        # --------------------------------------------------------

        terminated = (
            action == "TERMINATE_SESSION"
        )

        truncated = (
            self.state.step_count
            >= self.MAX_STEPS
        )

        done = terminated or truncated

        # --------------------------------------------------------
        # Reward
        # --------------------------------------------------------

        reward = SecurityReward.calculate(
            previous_threat=previous_threat,
            next_threat=self.state.threat,
            action=action,
            trust_score=previous_trust,
            next_trust_score=self.state.trust,
            terminated=terminated,
            previous_action=previous_action,
            recovery_phase=self.state.recovery_phase,
        )

        info = {
            "scenario": self.scenario.name,
            "trust_score": round(
                self.state.trust,
                2,
            ),
            "threat": round(
                self.state.threat,
                2,
            ),
            "previous_threat": round(
                previous_threat,
                2,
            ),
            "previous_trust": round(
                previous_trust,
                2,
            ),
            "previous_action": previous_action,
            "recovery_phase": self.state.recovery_phase,
            "terminated": terminated,
            "step": self.state.step_count,
        }

        return (
            self._encode_state(),
            reward,
            done,
            info,
        )

    # ============================================================
    # CANONICAL STATE ENCODING
    # ============================================================

    def _encode_state(self) -> str:

        if self.state is None:
            raise RuntimeError(
                "Environment has not been reset."
            )

        state = self.state

        security_state = SecurityState.from_observation(
            trust_score=state.trust,
            threat_score=state.threat,
            previous_trust_score=state.previous_trust,
            behavioral_risk=state.behavioral_risk,
            contextual_risk=state.device_risk,
            transaction_risk=(
                state.transaction_risk * 33.333
            ),
            previous_action=state.previous_action,
            pqc_enabled=(
                state.previous_action
                == "HYBRID_PQC"
            ),
        )

        return security_state.encode()

    # ============================================================
    # UTILITIES
    # ============================================================

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                100.0,
                float(value),
            ),
        )