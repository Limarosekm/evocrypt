from evocrypt.rl.agent import AdaptivePolicyAgent
from evocrypt.rl.environment import EvoCryptEnvironment


POLICY_PATH = "evocrypt_policy.json"


def main():
    agent = AdaptivePolicyAgent(seed=42)
    agent.load(POLICY_PATH)

    env = EvoCryptEnvironment(seed=42)

    scenarios = [
        "normal",
        "behavioral_anomaly",
        "device_takeover",
        "high_value_transaction",
        "combined_attack",
    ]

    print()
    print("=" * 80)
    print("EVOCRYPT RL POLICY EVALUATION")
    print("=" * 80)

    for scenario in scenarios:

        state = env.reset(scenario)

        print()
        print(f"SCENARIO: {scenario}")
        print("-" * 80)

        total_reward = 0.0

        for step in range(12):

            action = agent.choose_action(
                state,
                explore=False,
            )

            safe_action = agent.safe_action(
                env.trust_score,
                action,
            )

            next_state, reward, done, info = env.step(
                safe_action
            )

            total_reward += reward

            print(
                f"Step {step + 1:02d} | "
                f"Trust={info['trust_score']:6.2f} | "
                f"Threat={info['threat']:6.2f} | "
                f"RL={action:18s} | "
                f"Final={safe_action:18s} | "
                f"Reward={reward:7.2f}"
            )

            state = next_state

            if done:
                break

        print("-" * 80)
        print(f"Total reward: {total_reward:.2f}")


if __name__ == "__main__":
    main()