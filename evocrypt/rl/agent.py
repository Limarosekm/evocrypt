from typing import Dict, List, Optional
import random


class AdaptivePolicyAgent:
    """
    Lightweight Q-Learning agent for EvoCrypt.

    The agent receives a trust state and selects the most
    appropriate security action.

    States:

        VERY_LOW
        LOW
        MEDIUM
        HIGH

    Actions:

        NORMAL
        MONITOR
        ROTATE_KEY
        REAUTHENTICATE
        HYBRID_PQC
        TERMINATE_SESSION

    The Q-table is intentionally small so that training and
    inference remain lightweight.
    """

    # ============================================================
    # STATES
    # ============================================================

    STATES = [
        "HIGH",
        "MEDIUM",
        "LOW",
        "VERY_LOW",
    ]

    # ============================================================
    # ACTIONS
    # ============================================================

    ACTIONS = [
        "NORMAL",
        "MONITOR",
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    ]

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        learning_rate: float = 0.10,
        discount_factor: float = 0.90,
        exploration_rate: float = 0.10,
        exploration_decay: float = 0.995,
        minimum_exploration: float = 0.01,
    ):
        """
        Initialize the Q-learning agent.

        Args:
            learning_rate:
                How strongly new experiences modify the Q-table.

            discount_factor:
                Importance of future rewards.

            exploration_rate:
                Probability of trying a random action.

            exploration_decay:
                Reduces exploration after training.

            minimum_exploration:
                Minimum amount of exploration allowed.
        """

        self.learning_rate = float(
            learning_rate
        )

        self.discount_factor = float(
            discount_factor
        )

        self.exploration_rate = float(
            exploration_rate
        )

        self.exploration_decay = float(
            exploration_decay
        )

        self.minimum_exploration = float(
            minimum_exploration
        )

        # --------------------------------------------------------
        # Q-table
        # --------------------------------------------------------

        self.q_table: Dict[str, Dict[str, float]] = {
            state: {
                action: 0.0
                for action in self.ACTIONS
            }
            for state in self.STATES
        }

        # --------------------------------------------------------
        # Training statistics
        # --------------------------------------------------------

        self.training_steps = 0

    # ============================================================
    # TRUST → STATE
    # ============================================================

    def state_from_trust(
        self,
        trust_score: float
    ) -> str:
        """
        Convert a numerical trust score into an RL state.

        Mapping:

            70-100 → HIGH
            40-69  → MEDIUM
            20-39  → LOW
            0-19   → VERY_LOW
        """

        try:
            score = float(
                trust_score
            )

        except (
            TypeError,
            ValueError
        ):
            score = 0.0

        score = max(
            0.0,
            min(
                100.0,
                score
            )
        )

        if score >= 70:
            return "HIGH"

        if score >= 40:
            return "MEDIUM"

        if score >= 20:
            return "LOW"

        return "VERY_LOW"

    # ============================================================
    # ACTION SELECTION
    # ============================================================

    def choose_action(
        self,
        state: str,
        explore: bool = False
    ) -> str:
        """
        Select an action for the current state.

        Args:
            state:
                Current RL state.

            explore:
                If True, epsilon-greedy exploration is enabled.

                Runtime EvoCrypt normally uses:
                    explore=False

                Training normally uses:
                    explore=True
        """

        state = self._normalize_state(
            state
        )

        # --------------------------------------------------------
        # Exploration
        # --------------------------------------------------------

        if (
            explore
            and
            random.random() <
            self.exploration_rate
        ):
            return random.choice(
                self.ACTIONS
            )

        # --------------------------------------------------------
        # Exploitation
        # --------------------------------------------------------

        values = self.q_table[
            state
        ]

        # --------------------------------------------------------
        # SAFE DEFAULT BEFORE RL TRAINING
        # --------------------------------------------------------
        # When all Q-values are zero, the agent has not learned
        # anything yet. Do not randomly select an action.

        if all(
            value == 0.0
            for value in values.values()
        ):
            return "NORMAL"

        maximum = max(
            values.values()
        )

        # --------------------------------------------------------
        # RANDOM TIE BREAKING
        # --------------------------------------------------------

        best_actions = [
            action
            for action, value
            in values.items()
            if value == maximum
        ]

        return random.choice(
            best_actions
        )

    # ============================================================
    # Q-LEARNING UPDATE
    # ============================================================

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        done: bool = False
    ) -> float:
        """
        Perform one Q-learning update.

        Formula:

        Q(s,a) =
            Q(s,a)
            +
            α[
                r
                +
                γ max Q(s',a')
                -
                Q(s,a)
            ]

        If the episode is finished:

            Q(s,a) =
                Q(s,a)
                +
                α[
                    r -
                    Q(s,a)
                ]

        Returns:
            Updated Q-value.
        """

        state = self._normalize_state(
            state
        )

        next_state = self._normalize_state(
            next_state
        )

        action = self._normalize_action(
            action
        )

        try:
            reward = float(
                reward
            )

        except (
            TypeError,
            ValueError
        ):
            reward = 0.0

        current_q = self.q_table[
            state
        ][
            action
        ]

        # --------------------------------------------------------
        # TERMINAL STATE
        # --------------------------------------------------------

        if done:

            target = reward

        # --------------------------------------------------------
        # NON-TERMINAL STATE
        # --------------------------------------------------------

        else:

            next_best_q = max(
                self.q_table[
                    next_state
                ].values()
            )

            target = (
                reward
                +
                self.discount_factor
                *
                next_best_q
            )

        # --------------------------------------------------------
        # Q-LEARNING FORMULA
        # --------------------------------------------------------

        new_q = (
            current_q
            +
            self.learning_rate
            *
            (
                target
                -
                current_q
            )
        )

        self.q_table[
            state
        ][
            action
        ] = new_q

        self.training_steps += 1

        return new_q

    # ============================================================
    # TRAINING EPISODE
    # ============================================================

    def train_episode(
        self,
        transitions: List[dict]
    ) -> Dict[str, float]:
        """
        Train the agent using a list of recorded transitions.

        Example:

            transitions = [
                {
                    "state": "HIGH",
                    "action": "MONITOR",
                    "reward": 3,
                    "next_state": "HIGH"
                },
                {
                    "state": "HIGH",
                    "action": "ROTATE_KEY",
                    "reward": 5,
                    "next_state": "MEDIUM"
                }
            ]

        Returns training statistics.
        """

        total_reward = 0.0

        for transition in transitions:

            state = transition.get(
                "state",
                "HIGH"
            )

            action = transition.get(
                "action",
                "MONITOR"
            )

            reward = transition.get(
                "reward",
                0
            )

            next_state = transition.get(
                "next_state",
                state
            )

            done = bool(
                transition.get(
                    "done",
                    False
                )
            )

            self.update(
                state,
                action,
                reward,
                next_state,
                done
            )

            try:
                total_reward += float(
                    reward
                )

            except (
                TypeError,
                ValueError
            ):
                pass

        # --------------------------------------------------------
        # Reduce exploration after episode
        # --------------------------------------------------------

        self.decay_exploration()

        return {
            "steps": len(
                transitions
            ),

            "total_reward":
                round(
                    total_reward,
                    3
                ),

            "exploration_rate":
                round(
                    self.exploration_rate,
                    5
                )
        }

    # ============================================================
    # EXPLORATION DECAY
    # ============================================================

    def decay_exploration(
        self
    ):
        """
        Reduce exploration after a training iteration.
        """

        self.exploration_rate = max(
            self.minimum_exploration,
            self.exploration_rate
            *
            self.exploration_decay
        )

    # ============================================================
    # GET Q-TABLE
    # ============================================================

    def get_q_table(
        self
    ) -> Dict[str, Dict[str, float]]:
        """
        Return a copy of the current Q-table.
        """

        return {
            state: dict(
                actions
            )
            for state, actions
            in self.q_table.items()
        }

    # ============================================================
    # BEST POLICY
    # ============================================================

    def get_policy(
        self
    ) -> Dict[str, str]:
        """
        Return the current best action for every state.
        """

        policy = {}

        for state in self.STATES:

            policy[state] = (
                self.choose_action(
                    state,
                    explore=False
                )
            )

        return policy

    # ============================================================
    # SET Q-VALUE
    # ============================================================

    def set_q_value(
        self,
        state: str,
        action: str,
        value: float
    ):
        """
        Manually set a Q-value.

        Useful for experiments and initializing a policy.
        """

        state = self._normalize_state(
            state
        )

        action = self._normalize_action(
            action
        )

        self.q_table[
            state
        ][
            action
        ] = float(
            value
        )

    # ============================================================
    # RESET
    # ============================================================

    def reset(
        self
    ):
        """
        Reset the Q-table and training statistics.
        """

        self.q_table = {
            state: {
                action: 0.0
                for action in self.ACTIONS
            }
            for state in self.STATES
        }

        self.training_steps = 0

    # ============================================================
    # ACTION SAFETY POLICY
    # ============================================================

    def safe_action(
        self,
        trust_score: float,
        selected_action: Optional[str]
    ) -> str:
        """
        Apply mandatory safety boundaries around the learned policy.

        RL should not be allowed to make an obviously unsafe
        decision simply because of a poorly trained Q-table.

        Rules:

            Very low trust:
                TERMINATE_SESSION

            Low trust:
                at least HYBRID_PQC

            Medium trust:
                at least MONITOR

            High trust:
                learned policy may be used
        """

        state = self.state_from_trust(
            trust_score
        )

        action = self._normalize_action(
            selected_action
        )

        # --------------------------------------------------------
        # Critical trust
        # --------------------------------------------------------

        if state == "VERY_LOW":

            return "TERMINATE_SESSION"

        # --------------------------------------------------------
        # Low trust
        # --------------------------------------------------------

        if state == "LOW":

            if action in {
                "NORMAL",
                "MONITOR"
            }:
                return "HYBRID_PQC"

        # --------------------------------------------------------
        # Medium trust
        # --------------------------------------------------------

        if state == "MEDIUM":

            if action == "NORMAL":

                return "MONITOR"

        # --------------------------------------------------------
        # High trust
        # --------------------------------------------------------

        return action

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def export_q_table(
        self
    ) -> dict:
        """
        Return a serializable representation of the agent.

        This can later be stored as JSON.
        """

        return {
            "learning_rate":
                self.learning_rate,

            "discount_factor":
                self.discount_factor,

            "exploration_rate":
                self.exploration_rate,

            "exploration_decay":
                self.exploration_decay,

            "minimum_exploration":
                self.minimum_exploration,

            "training_steps":
                self.training_steps,

            "q_table":
                self.get_q_table()
        }

    # ============================================================
    # INTERNAL NORMALIZATION
    # ============================================================

    def _normalize_state(
        self,
        state: str
    ) -> str:

        if not isinstance(
            state,
            str
        ):
            return "HIGH"

        state = state.upper().strip()

        aliases = {
            "VERY LOW":
                "VERY_LOW",

            "CRITICAL":
                "VERY_LOW",

            "HIGH_RISK":
                "LOW",

            "MEDIUM_RISK":
                "MEDIUM",

            "LOW_RISK":
                "HIGH"
        }

        state = aliases.get(
            state,
            state
        )

        if state not in self.STATES:

            return "HIGH"

        return state

    # ============================================================
    # ACTION NORMALIZATION
    # ============================================================

    def _normalize_action(
        self,
        action: Optional[str]
    ) -> str:

        if not isinstance(
            action,
            str
        ):
            return "MONITOR"

        action = action.upper().strip()

        aliases = {
            "ROTATE":
                "ROTATE_KEY",

            "ROTATE-KEY":
                "ROTATE_KEY",

            "REAUTH":
                "REAUTHENTICATE",

            "PQC":
                "HYBRID_PQC",

            "HYBRID":
                "HYBRID_PQC",

            "TERMINATE":
                "TERMINATE_SESSION"
        }

        action = aliases.get(
            action,
            action
        )

        if action not in self.ACTIONS:

            return "MONITOR"

        return action