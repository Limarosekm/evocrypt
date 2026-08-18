from evocrypt.rl.environment import EvoCryptEnvironment
from evocrypt.rl.policy import AdaptiveSecurityPolicy
from evocrypt.rl.agent import AdaptivePolicyAgent


def main():
    env = EvoCryptEnvironment(seed=42)

    policy = AdaptiveSecurityPolicy(
        AdaptivePolicyAgent()
    )

    scenarios = [
        "normal",
        "behavioral_anomaly",
        "device_takeover",
        "high_value_transaction",
        "combined_attack",
    ]

    print("=" * 75)
    print("EVOCRYPT V3 STATE CONSISTENCY CHECK")
    print("=" * 75)

    failures = 0

    for scenario in scenarios:

        environment_state = env.reset(
            scenario
        )

        observation = env.state

        policy_state = policy._build_state(
            trust_score=observation.trust,
            threat_score=observation.threat,
            behavioral_risk=observation.behavioral_risk,
            device_risk=observation.device_risk,
            transaction_risk=observation.transaction_risk,
            recovery_phase=observation.recovery_phase,
            previous_action=observation.previous_action,
            stability_steps=observation.step_count,
        )

        match = (
            environment_state
            == policy_state
        )

        print()
        print(f"Scenario: {scenario}")
        print(f"Environment: {environment_state}")
        print(f"Policy:      {policy_state}")
        print(f"MATCH:       {match}")

        if not match:
            failures += 1

    print()
    print("=" * 75)

    if failures == 0:
        print("RESULT: ALL STATES MATCH")
    else:
        print(
            f"RESULT: {failures} STATE MISMATCHES"
        )


if __name__ == "__main__":
    main()