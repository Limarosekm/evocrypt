from pathlib import Path

from evocrypt.rl import (
    AdaptiveSecurityPolicy,
    SecurityDecision,
)


def test_policy_decision_structure():

    policy = AdaptiveSecurityPolicy(
        agent=__import__(
            "evocrypt.rl",
            fromlist=[
                "AdaptivePolicyAgent"
            ]
        ).AdaptivePolicyAgent()
    )

    decision = policy.decide(
        trust_score=85,
        threat_score=10,
    )

    assert isinstance(
        decision,
        SecurityDecision
    )

    assert decision.action in (
        "NORMAL",
        "MONITOR",
        "ROTATE_KEY",
        "REAUTHENTICATE",
        "HYBRID_PQC",
        "TERMINATE_SESSION",
    )

    assert 0 <= decision.confidence <= 1


def test_critical_trust_is_never_allowed_normal():

    from evocrypt.rl import AdaptivePolicyAgent

    policy = AdaptiveSecurityPolicy(
        AdaptivePolicyAgent()
    )

    decision = policy.decide(
        trust_score=10,
        threat_score=90,
    )

    assert (
        decision.action
        == "TERMINATE_SESSION"
    )


def test_medium_trust_is_never_allowed_normal():

    from evocrypt.rl import AdaptivePolicyAgent

    policy = AdaptiveSecurityPolicy(
        AdaptivePolicyAgent()
    )

    decision = policy.decide(
        trust_score=50,
        threat_score=45,
    )

    assert decision.action != "NORMAL"


def test_state_contains_security_features():

    from evocrypt.rl import AdaptivePolicyAgent

    policy = AdaptiveSecurityPolicy(
        AdaptivePolicyAgent()
    )

    decision = policy.decide(
        trust_score=45,
        threat_score=65,
        behavioral_risk=2,
        device_risk=3,
        transaction_risk=1,
        recovery_phase=1,
        previous_action="MONITOR",
        stability_steps=2,
    )

    assert decision.state.startswith(
        "v3|"
    )

    assert "|b2|" in decision.state
    assert "|c3|" in decision.state
    assert "|x1|" in decision.state
    assert "|r1|" in decision.state
    assert "|s2|" in decision.state