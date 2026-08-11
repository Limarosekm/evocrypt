from typing import Any, Dict, Optional


class TrustScorer:
    """
    EvoCrypt Hybrid Trust Evaluation Engine.

    The TrustScorer converts behavioral and contextual
    session signals into an explainable trust score.

    Input:
        Behavioral signals
        Contextual signals
        Previous trust score

    Output:
        Updated trust score
        Risk level
        Risk penalty
        Explanation/reasons

    Trust score range:

        100  -> Very trusted
        70+  -> Low risk
        40-69 -> Medium risk
        20-39 -> High risk
        0-19  -> Critical risk
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        low_threshold: float = 40.0,
        critical_threshold: float = 20.0
    ):
        """
        Initialize the trust engine.

        Args:
            low_threshold:
                Threshold below which the session enters
                a higher-risk state.

            critical_threshold:
                Threshold below which the session is
                considered critical.
        """

        self.low_threshold = float(
            low_threshold
        )

        self.critical_threshold = float(
            critical_threshold
        )

    # ============================================================
    # MAIN TRUST EVALUATION
    # ============================================================

    def evaluate(
        self,
        signals: Dict[str, Any],
        previous_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a new behavioral observation.

        Args:
            signals:
                Behavioral measurements collected from
                the client.

            previous_score:
                Trust score from the previous evaluation.

            context:
                Additional contextual security signals.

        Example signals:

            {
                "typing_speed": 5.2,
                "avg_key_hold": 110,
                "mouse_speed": 250,
                "mouse_distance": 1200,
                "click_count": 15,
                "scroll_distance": 300,
                "idle_time": 4,
                "suspicious": False
            }

        Example context:

            {
                "ip_changed": False,
                "device_changed": False,
                "unusual_time": False,
                "transaction_risk": "LOW"
            }

        Returns:

            {
                "score": 82.4,
                "status": "HIGH",
                "penalty": 10,
                "reasons": [...]
            }
        """

        # --------------------------------------------------------
        # Normalize inputs
        # --------------------------------------------------------

        signals = signals or {}

        context = context or {}

        previous_score = self._clamp_score(
            previous_score
        )

        # --------------------------------------------------------
        # Calculate behavioral risk
        # --------------------------------------------------------

        behavioral_penalty, behavioral_reasons = (
            self._evaluate_behavior(
                signals
            )
        )

        # --------------------------------------------------------
        # Calculate contextual risk
        # --------------------------------------------------------

        contextual_penalty, contextual_reasons = (
            self._evaluate_context(
                context
            )
        )

        # --------------------------------------------------------
        # Combine risk
        # --------------------------------------------------------

        total_penalty = (
            behavioral_penalty +
            contextual_penalty
        )

        reasons = (
            behavioral_reasons +
            contextual_reasons
        )

        # --------------------------------------------------------
        # Calculate new trust score
        # --------------------------------------------------------
        #
        # We don't immediately destroy the entire trust score.
        # This provides smoother continuous authentication.
        #
        # Example:
        #
        # Previous = 88
        # Penalty  = 10
        #
        # New ≈ 82.5
        #
        # This prevents one small measurement variation from
        # instantly terminating a legitimate user.
        # --------------------------------------------------------

        new_score = (
            previous_score -
            total_penalty * 0.55
        )

        new_score = self._clamp_score(
            new_score
        )

        # --------------------------------------------------------
        # No suspicious behavior
        # --------------------------------------------------------

        if not reasons:

            reasons = [
                "Behavior remains within "
                "the expected session baseline"
            ]

        # --------------------------------------------------------
        # Determine risk level
        # --------------------------------------------------------

        risk_level = self._risk_level(
            new_score
        )

        return {

            "score":
                round(
                    new_score,
                    1
                ),

            "status":
                risk_level,

            "penalty":
                round(
                    total_penalty,
                    2
                ),

            "reasons":
                reasons,

            "behavioral_penalty":
                round(
                    behavioral_penalty,
                    2
                ),

            "contextual_penalty":
                round(
                    contextual_penalty,
                    2
                )
        }

    # ============================================================
    # BEHAVIOR ANALYSIS
    # ============================================================

    def _evaluate_behavior(
        self,
        signals: Dict[str, Any]
    ):
        """
        Evaluate behavioral biometric signals.

        Current signals:

            typing_speed
            avg_key_hold
            mouse_speed
            mouse_distance
            click_count
            scroll_distance
            idle_time
            suspicious

        Returns:

            penalty,
            reasons
        """

        penalty = 0.0

        reasons = []

        # --------------------------------------------------------
        # Typing speed
        # --------------------------------------------------------

        typing_speed = self._number(
            signals.get(
                "typing_speed"
            )
        )

        if typing_speed is not None:

            # Extremely slow or extremely fast typing
            # is treated as unusual.

            if (
                typing_speed < 0.5
                or
                typing_speed > 25
            ):

                penalty += 8

                reasons.append(
                    "Unusual typing cadence"
                )

        # --------------------------------------------------------
        # Average key hold duration
        # --------------------------------------------------------

        avg_key_hold = self._number(
            signals.get(
                "avg_key_hold"
            )
        )

        if avg_key_hold is not None:

            if (
                avg_key_hold < 25
                or
                avg_key_hold > 450
            ):

                penalty += 7

                reasons.append(
                    "Unusual key-hold duration"
                )

        # --------------------------------------------------------
        # Mouse / pointer speed
        # --------------------------------------------------------

        mouse_speed = self._number(
            signals.get(
                "mouse_speed"
            )
        )

        if mouse_speed is not None:

            if mouse_speed > 1800:

                penalty += 8

                reasons.append(
                    "Unusual pointer velocity"
                )

        # --------------------------------------------------------
        # Mouse travel distance
        # --------------------------------------------------------

        mouse_distance = self._number(
            signals.get(
                "mouse_distance"
            )
        )

        if mouse_distance is not None:

            if mouse_distance > 15000:

                penalty += 5

                reasons.append(
                    "Unusual pointer movement volume"
                )

        # --------------------------------------------------------
        # Click frequency
        # --------------------------------------------------------

        click_count = self._number(
            signals.get(
                "click_count"
            )
        )

        if click_count is not None:

            if click_count > 120:

                penalty += 5

                reasons.append(
                    "Unusual click frequency"
                )

        # --------------------------------------------------------
        # Scroll activity
        # --------------------------------------------------------

        scroll_distance = self._number(
            signals.get(
                "scroll_distance"
            )
        )

        if scroll_distance is not None:

            if scroll_distance > 30000:

                penalty += 3

                reasons.append(
                    "Unusual scrolling activity"
                )

        # --------------------------------------------------------
        # Idle time
        # --------------------------------------------------------

        idle_time = self._number(
            signals.get(
                "idle_time"
            )
        )

        if idle_time is not None:

            if idle_time > 120:

                penalty += 5

                reasons.append(
                    "Extended idle period"
                )

        # --------------------------------------------------------
        # Explicit suspicious flag
        # --------------------------------------------------------

        if self._boolean(
            signals.get(
                "suspicious"
            )
        ):

            penalty += 25

            reasons.append(
                "Suspicious behavior flag"
            )

        return (
            penalty,
            reasons
        )

    # ============================================================
    # CONTEXT ANALYSIS
    # ============================================================

    def _evaluate_context(
        self,
        context: Dict[str, Any]
    ):
        """
        Evaluate contextual security signals.

        Context signals include:

            IP changes
            Device changes
            Unusual login time
            Transaction risk
        """

        penalty = 0.0

        reasons = []

        # --------------------------------------------------------
        # IP / network change
        # --------------------------------------------------------

        if self._boolean(
            context.get(
                "ip_changed"
            )
        ):

            penalty += 18

            reasons.append(
                "Network context changed"
            )

        # --------------------------------------------------------
        # Device change
        # --------------------------------------------------------

        if self._boolean(
            context.get(
                "device_changed"
            )
        ):

            penalty += 20

            reasons.append(
                "Device context changed"
            )

        # --------------------------------------------------------
        # Unusual session time
        # --------------------------------------------------------

        if self._boolean(
            context.get(
                "unusual_time"
            )
        ):

            penalty += 6

            reasons.append(
                "Unusual session time"
            )

        # --------------------------------------------------------
        # Transaction risk
        # --------------------------------------------------------

        transaction_risk = (
            context.get(
                "transaction_risk"
            )
        )

        if isinstance(
            transaction_risk,
            str
        ):

            transaction_risk = (
                transaction_risk.upper()
            )

        if transaction_risk == "HIGH":

            penalty += 15

            reasons.append(
                "High-risk transaction"
            )

        elif transaction_risk == "MEDIUM":

            penalty += 7

            reasons.append(
                "Medium-risk transaction"
            )

        # --------------------------------------------------------
        # Geographic anomaly
        # --------------------------------------------------------

        if self._boolean(
            context.get(
                "location_changed"
            )
        ):

            penalty += 12

            reasons.append(
                "Location context changed"
            )

        # --------------------------------------------------------
        # Multiple simultaneous anomalies
        # --------------------------------------------------------

        anomaly_count = sum(
            [
                self._boolean(
                    context.get(
                        "ip_changed"
                    )
                ),

                self._boolean(
                    context.get(
                        "device_changed"
                    )
                ),

                self._boolean(
                    context.get(
                        "location_changed"
                    )
                ),

                self._boolean(
                    context.get(
                        "unusual_time"
                    )
                )
            ]
        )

        if anomaly_count >= 3:

            penalty += 10

            reasons.append(
                "Multiple contextual anomalies detected"
            )

        return (
            penalty,
            reasons
        )

    # ============================================================
    # RISK CLASSIFICATION
    # ============================================================

    def _risk_level(
        self,
        score: float
    ) -> str:
        """
        Convert a numerical trust score into
        a categorical risk level.
        """

        if score >= 70:

            return "LOW"

        if score >= self.low_threshold:

            return "MEDIUM"

        if score >= self.critical_threshold:

            return "HIGH"

        return "CRITICAL"

    # ============================================================
    # TRUST SCORE CLAMPING
    # ============================================================

    @staticmethod
    def _clamp_score(
        score: float
    ) -> float:
        """
        Keep trust score between 0 and 100.
        """

        try:

            score = float(
                score
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0.0

        return max(
            0.0,
            min(
                100.0,
                score
            )
        )

    # ============================================================
    # NUMERIC CONVERSION
    # ============================================================

    @staticmethod
    def _number(
        value
    ):
        """
        Safely convert a value into a float.

        Returns None when the value cannot be interpreted
        as a number.
        """

        if value is None:

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    # ============================================================
    # BOOLEAN CONVERSION
    # ============================================================

    @staticmethod
    def _boolean(
        value
    ) -> bool:
        """
        Safely interpret common boolean values.
        """

        if isinstance(
            value,
            bool
        ):

            return value

        if isinstance(
            value,
            str
        ):

            return value.lower() in {
                "true",
                "1",
                "yes",
                "on"
            }

        if isinstance(
            value,
            (int, float)
        ):

            return value != 0

        return False

    # ============================================================
    # DIRECT RISK CALCULATION
    # ============================================================

    def calculate_risk(
        self,
        score: float
    ) -> Dict[str, Any]:
        """
        Public helper for applications that already have
        a trust score.

        Example:

            scorer.calculate_risk(35)
        """

        score = self._clamp_score(
            score
        )

        return {

            "score":
                round(
                    score,
                    1
                ),

            "risk_level":
                self._risk_level(
                    score
                ),

            "is_low_risk":
                score >= 70,

            "is_medium_risk":
                (
                    score >= 40
                    and
                    score < 70
                ),

            "is_high_risk":
                (
                    score >= 20
                    and
                    score < 40
                ),

            "is_critical":
                score < 20
        }

    # ============================================================
    # TRUST RECOVERY
    # ============================================================

    def recover(
        self,
        current_score: float,
        recovery_rate: float = 2.0
    ) -> float:
        """
        Gradually recover trust when normal behavior
        continues.

        Example:

            55 → 57 → 59 → 61 ...

        Trust cannot exceed 100.
        """

        current_score = self._clamp_score(
            current_score
        )

        recovery_rate = max(
            0.0,
            float(recovery_rate)
        )

        return round(
            min(
                100.0,
                current_score +
                recovery_rate
            ),
            1
        )

    # ============================================================
    # EXPLANATION
    # ============================================================

    def explain(
        self,
        result: Dict[str, Any]
    ) -> str:
        """
        Convert a trust evaluation result into a
        human-readable explanation.

        Useful for the EvoCrypt dashboard.
        """

        score = result.get(
            "score",
            0
        )

        risk = result.get(
            "status",
            "UNKNOWN"
        )

        reasons = result.get(
            "reasons",
            []
        )

        if not reasons:

            return (
                f"Trust score is {score}/100. "
                f"Risk level: {risk}."
            )

        reason_text = "; ".join(
            reasons
        )

        return (
            f"Trust score is {score}/100. "
            f"Risk level: {risk}. "
            f"Reason: {reason_text}."
        )