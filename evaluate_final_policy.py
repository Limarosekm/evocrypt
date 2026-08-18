from evocrypt.rl.agent import AdaptivePolicyAgent
from evocrypt.rl.environment import EvoCryptEnvironment


POLICY_PATH = "evocrypt_policy_final.json"


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
    print("EVOCRYPT V3 FINAL RL POLICY EVALUATION")
    print("=" * 80)

    results = []

    for scenario in scenarios:

        state = env.reset(scenario)

        print()
        print(f"SCENARIO: {scenario}")
        print("-" * 80)

        total_reward = 0.0
        actions = []

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
            actions.append(safe_action)

            print(
                f"Step {step + 1:02d} | "
                f"Trust={info['trust_score']:6.2f} | "
                f"Threat={info['threat']:6.2f} | "
                f"RL={action:18s} | "
                f"Final={safe_action:18s} | "
                f"Reward={reward:8.2f}"
            )

            state = next_state

            if done:
                break

        results.append(
            {
                "scenario": scenario,
                "reward": total_reward,
                "steps": len(actions),
                "actions": actions,
                "final_trust": env.trust_score,
            }
        )

        print()
        print(
            f"Total reward: {total_reward:.2f}"
        )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for result in results:
        print(
            f"{result['scenario']:25s} | "
            f"Reward={result['reward']:8.2f} | "
            f"Steps={result['steps']:2d} | "
            f"Final Trust={result['final_trust']:6.2f}"
        )


if __name__ == "__main__":
    main()