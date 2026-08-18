from typing import Any, Dict


ACTION_COST = {
    "NORMAL": 0.0,
    "MONITOR": 0.8,
    "ROTATE_KEY": 2.0,
    "REAUTHENTICATE": 3.0,
    "HYBRID_PQC": 4.0,
    "TERMINATE_SESSION": 6.0,
}


APPROPRIATE_ACTIONS = {
    "NORMAL": {
        "NORMAL",
        "MONITOR",
    },
    "LOW": {
        "MONITOR",
        "ROTATE_KEY",
    },
    "MEDIUM": {
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
    },
    "HIGH": {
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    },
}


class SecurityReward:
    """
    Security-aware reward function.

    Objectives:

        1. Reduce genuine threats.
        2. Preserve legitimate sessions.
        3. Avoid unnecessary expensive interventions.
        4. Recover toward normal operation after mitigation.
        5. Penalize repeated intervention after recovery.
    """

    @staticmethod
    def calculate(
        *,
        previous_threat: float,
        next_threat: float,
        action: str,
        trust_score: float,
        next_trust_score: float,
        terminated: bool = False,
        previous_action: str = "NONE",
        recovery_phase: int = 0,
    ) -> float:

        previous_threat = max(
            0.0,
            min(
                100.0,
                float(previous_threat),
            ),
        )

        next_threat = max(
            0.0,
            min(
                100.0,
                float(next_threat),
            ),
        )

        trust_score = max(
            0.0,
            min(
                100.0,
                float(trust_score),
            ),
        )

        next_trust_score = max(
            0.0,
            min(
                100.0,
                float(next_trust_score),
            ),
        )

        threat_reduction = (
            previous_threat
            - next_threat
        )

        trust_change = (
            next_trust_score
            - trust_score
        )

        reward = 0.0

        # ========================================================
        # THREAT MITIGATION
        # ========================================================

        reward += (
            threat_reduction
            * 0.35
        )

        # ========================================================
        # TRUST RECOVERY
        # ========================================================

        reward += (
            trust_change
            * 0.12
        )

        # ========================================================
        # ACTION COST
        # ========================================================

        reward -= ACTION_COST.get(
            action,
            3.0,
        )

        # ========================================================
        # NORMAL OPERATION
        # ========================================================

        if previous_threat < 15:

            if action == "NORMAL":
                reward += 5.0

            elif action == "MONITOR":
                reward += 1.0

            elif action in {
                "ROTATE_KEY",
                "REAUTHENTICATE",
                "HYBRID_PQC",
            }:
                reward -= 6.0

            elif action == "TERMINATE_SESSION":
                reward -= 25.0

        # ========================================================
        # LOW THREAT
        # ========================================================

        elif previous_threat < 30:

            if action in {
                "MONITOR",
                "NORMAL",
            }:
                reward += 2.0

            if action == "HYBRID_PQC":
                reward -= 5.0

            if action == "TERMINATE_SESSION":
                reward -= 18.0

        # ========================================================
        # MEDIUM THREAT
        # ========================================================

        elif previous_threat < 60:

            if action in {
                "MONITOR",
                "ROTATE_KEY",
                "REAUTHENTICATE",
                "HYBRID_PQC",
            }:
                reward += 3.0

            if action == "NORMAL":
                reward -= 6.0

            if action == "TERMINATE_SESSION":
                reward -= 8.0

        # ========================================================
        # HIGH THREAT
        # ========================================================

        else:

            if action in {
                "REAUTHENTICATE",
                "HYBRID_PQC",
                "TERMINATE_SESSION",
            }:
                reward += 8.0

            if action == "NORMAL":
                reward -= 15.0

            elif action == "MONITOR":
                reward -= 5.0

        # ========================================================
        # TERMINATION
        # ========================================================

        if terminated:

            if previous_threat >= 75:
                reward += 15.0
            else:
                reward -= 20.0

        # ========================================================
        # REPEATED EXPENSIVE ACTION
        # ========================================================

        if (
            previous_action == action
            and action in {
                "ROTATE_KEY",
                "REAUTHENTICATE",
                "HYBRID_PQC",
            }
        ):
            reward -= 2.5

        # ========================================================
        # RECOVERY PHASE
        # ========================================================

        if recovery_phase == 2:

            if action == "NORMAL":
                reward += 3.0

            elif action == "MONITOR":
                reward += 1.0

            elif action in {
                "ROTATE_KEY",
                "REAUTHENTICATE",
                "HYBRID_PQC",
            }:
                reward -= 4.0

            elif action == "TERMINATE_SESSION":
                reward -= 15.0

        return round(
            reward,
            4,
        )

    @staticmethod
    def explain(
        *,
        previous_threat: float,
        next_threat: float,
        action: str,
        reward: float,
    ) -> Dict[str, Any]:

        return {
            "previous_threat": round(
                previous_threat,
                2,
            ),
            "next_threat": round(
                next_threat,
                2,
            ),
            "threat_delta": round(
                next_threat - previous_threat,
                2,
            ),
            "action": action,
            "reward": round(
                reward,
                4,
            ),
            "action_cost": ACTION_COST.get(
                action,
                3.0,
            ),
        }