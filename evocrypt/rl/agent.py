from typing import Dict, List, Optional, Any
import json
import random


class AdaptivePolicyAgent:
    """
    Tabular Q-learning policy engine for EvoCrypt.

    Backward compatibility:
      - The original four trust states are still supported.
      - Existing tests using state_from_trust(), q_table and set_q_value()
        continue to work.

    New behavior:
      - Arbitrary encoded SecurityState strings can be used as states.
      - States are created lazily.
      - Q-values can be inspected at runtime.
      - Policies can be exported/imported as JSON.
      - A simple confidence score is exposed for the dashboard.
    """

    STATES = [
        "HIGH",
        "MEDIUM",
        "LOW",
        "VERY_LOW",
    ]

    ACTIONS = [
        "NORMAL",
        "MONITOR",
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    ]

    def __init__(
        self,
        learning_rate: float = 0.10,
        discount_factor: float = 0.90,
        exploration_rate: float = 0.20,
        exploration_decay: float = 0.995,
        minimum_exploration: float = 0.02,
        seed: Optional[int] = 42,
    ):
        self.learning_rate = float(learning_rate)
        self.discount_factor = float(discount_factor)
        self.exploration_rate = float(exploration_rate)
        self.exploration_decay = float(exploration_decay)
        self.minimum_exploration = float(minimum_exploration)

        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = random.Random()

        self.q_table: Dict[str, Dict[str, float]] = {
            state: {action: 0.0 for action in self.ACTIONS}
            for state in self.STATES
        }

        self.training_steps = 0
        self.episodes = 0

    def _ensure_state(self, state: str) -> str:
        state = str(state or "HIGH")
        if state not in self.q_table:
            self.q_table[state] = {
                action: 0.0 for action in self.ACTIONS
            }
        return state

    def state_from_trust(self, trust_score: float) -> str:
        try:
            score = float(trust_score)
        except (TypeError, ValueError):
            score = 0.0

        score = max(0.0, min(100.0, score))

        if score >= 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        if score >= 20:
            return "LOW"
        return "VERY_LOW"

    def choose_action(
        self,
        state: str,
        explore: bool = False,
        allowed_actions: Optional[List[str]] = None,
    ) -> str:
        state = self._ensure_state(
        state
    )
        self._ensure_state(state)

        actions = [
            self._normalize_action(action)
            for action in (allowed_actions or self.ACTIONS)
        ]
        actions = [a for a in actions if a in self.ACTIONS]
        if not actions:
            actions = list(self.ACTIONS)

        if explore and self._rng.random() < self.exploration_rate:
            return self._rng.choice(actions)

        values = self.q_table[state]

        # Before training, use a deterministic safe default.
        if all(values[action] == 0.0 for action in actions):
            return "MONITOR" if "MONITOR" in actions else actions[0]

        maximum = max(values[action] for action in actions)
        best_actions = [
            action for action in actions
            if values[action] == maximum
        ]

        return self._rng.choice(best_actions)

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        done: bool = False,
    ) -> float:
        state = self._ensure_state(
    state
)

        next_state = self._ensure_state(
            next_state
        )
        action = self._normalize_action(action)

        self._ensure_state(state)
        self._ensure_state(next_state)

        try:
            reward = float(reward)
        except (TypeError, ValueError):
            reward = 0.0

        current_q = self.q_table[state][action]

        if done:
            target = reward
        else:
            next_best_q = max(self.q_table[next_state].values())
            target = reward + self.discount_factor * next_best_q

        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_table[state][action] = new_q
        self.training_steps += 1

        return new_q

    def train_episode(self, transitions: List[dict]) -> Dict[str, float]:
        total_reward = 0.0

        for transition in transitions:
            state = transition.get("state", "HIGH")
            action = transition.get("action", "MONITOR")
            reward = transition.get("reward", 0)
            next_state = transition.get("next_state", state)
            done = bool(transition.get("done", False))

            self.update(state, action, reward, next_state, done)

            try:
                total_reward += float(reward)
            except (TypeError, ValueError):
                pass

        self.episodes += 1
        self.decay_exploration()

        return {
            "steps": len(transitions),
            "total_reward": round(total_reward, 3),
            "exploration_rate": round(self.exploration_rate, 5),
        }

    def decay_exploration(self):
        self.exploration_rate = max(
            self.minimum_exploration,
            self.exploration_rate * self.exploration_decay,
        )

    def get_q_table(self) -> Dict[str, Dict[str, float]]:
        return {
            state: dict(actions)
            for state, actions in self.q_table.items()
        }

    def get_q_values(self, state: str) -> Dict[str, float]:
        state = self._normalize_state(state)
        self._ensure_state(state)
        return dict(self.q_table[state])

    def get_policy(
        self
    ) -> Dict[str, str]:

        policy = {}

        for state in self.q_table:

            policy[state] = (
                self.choose_action(
                    state,
                    explore=False
                )
            )

        return policy

    def confidence(self, state: str) -> float:
        """
        Relative confidence based on the separation between the best
        and second-best Q-values. This is not a calibrated probability.
        """
        values = sorted(
            self.get_q_values(state).values(),
            reverse=True,
        )

        if not values:
            return 0.0

        if len(values) == 1:
            return 1.0

        best = values[0]
        second = values[1]
        spread = abs(best) + abs(second) + 1e-9

        return round(max(0.0, min(1.0, (best - second) / spread + 0.5)), 3)

    def set_q_value(self, state: str, action: str, value: float):
        state = self._ensure_state(
    state
)
        action = self._normalize_action(action)
        self._ensure_state(state)
        self.q_table[state][action] = float(value)

    def reset(self):
        self.q_table = {
            state: {action: 0.0 for action in self.ACTIONS}
            for state in self.STATES
        }
        self.training_steps = 0
        self.episodes = 0

    def safe_action(
        self,
        trust_score: float,
        selected_action: Optional[str],
    ) -> str:
        """
        Deterministic security guardrail around the learned policy.
        """

        state = self.state_from_trust(trust_score)
        action = self._normalize_action(selected_action)

        if state == "VERY_LOW":
            return "TERMINATE_SESSION"

        if state == "LOW" and action in {"NORMAL", "MONITOR"}:
            return "HYBRID_PQC"

        if state == "MEDIUM" and action == "NORMAL":
            return "MONITOR"

        return action

    def export_q_table(self) -> dict:
        return {
            "version": 2,
            "algorithm": "tabular_q_learning",
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "exploration_rate": self.exploration_rate,
            "minimum_exploration": self.minimum_exploration,
            "training_steps": self.training_steps,
            "episodes": self.episodes,
            "q_table": self.get_q_table(),
        }

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.export_q_table(), handle, indent=2)

    def load(self, path: str):
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        table = payload.get("q_table", {})
        if not isinstance(table, dict):
            raise ValueError("Invalid EvoCrypt policy file")

        self.q_table = {
            str(state): {
                self._normalize_action(action): float(value)
                for action, value in values.items()
                if self._normalize_action(action) in self.ACTIONS
            }
            for state, values in table.items()
        }

        for state in self.STATES:
            self._ensure_state(state)

        self.training_steps = int(payload.get("training_steps", 0))
        self.episodes = int(payload.get("episodes", 0))
    def _normalize_state(
        self,
        state: str,
    ) -> str:
        """
        Normalize EvoCrypt RL states.

        Legacy trust states use uppercase names.

        Structured v3 states use lowercase canonical
        representation so they remain compatible with
        the trained policy file.
        """

        if not isinstance(state, str):
            return "HIGH"

        state = state.strip()

        # --------------------------------------------------------
        # Structured states
        # --------------------------------------------------------

        if state.lower().startswith(("v2|", "v3|")):
            return state.lower()

        # --------------------------------------------------------
        # Legacy states
        # --------------------------------------------------------

        state = state.upper()

        aliases = {
            "VERY LOW": "VERY_LOW",
            "CRITICAL": "VERY_LOW",
            "HIGH_RISK": "LOW",
            "MEDIUM_RISK": "MEDIUM",
            "LOW_RISK": "HIGH",
        }

        state = aliases.get(
            state,
            state,
        )

        if state in self.STATES:
            return state

        return "HIGH"

    def _normalize_action(self, action: Optional[str]) -> str:
        if not isinstance(action, str):
            return "MONITOR"

        action = action.upper().strip()

        aliases = {
            "ROTATE": "ROTATE_KEY",
            "ROTATE-KEY": "ROTATE_KEY",
            "REAUTH": "REAUTHENTICATE",
            "PQC": "HYBRID_PQC",
            "HYBRID": "HYBRID_PQC",
            "TERMINATE": "TERMINATE_SESSION",
        }

        action = aliases.get(action, action)

        if action not in self.ACTIONS:
            return "MONITOR"

        return action
    def _ensure_state(
        self,
        state: str
    ) -> str:
        """
        Ensure that a state exists in the Q-table.

        This keeps the agent backward compatible with the
        original four trust states while supporting the
        structured EvoCrypt state space.
        """

        state = self._normalize_state(
            state
        )

        if state not in self.q_table:
            self.q_table[state] = {
                action: 0.0
                for action in self.ACTIONS
            }

        return state
    def has_state(
        self,
        state: str,
    ) -> bool:
        """
        Return True when the policy has learned the supplied state.
        """

        normalized = self._normalize_state(
            state
        )

        return normalized in self.q_table
    def get_q_values(
        self,
        state: str,
    ) -> Dict[str, float]:
        """
        Return learned Q-values for a state.

        Unknown states return zero-valued actions without
        mutating the Q-table.
        """

        normalized = self._normalize_state(
            state
        )

        values = self.q_table.get(
            normalized
        )

        if values is None:
            return {
                action: 0.0
                for action in self.ACTIONS
            }

        return dict(values)
