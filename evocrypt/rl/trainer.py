import argparse
from typing import Dict, Iterable, Optional

from .agent import AdaptivePolicyAgent
from .environment import EvoCryptEnvironment, SCENARIOS


def train_agent(
    *,
    episodes: int = 3000,
    seed: int = 42,
    scenario_names: Optional[Iterable[str]] = None,
) -> Dict:

    agent = AdaptivePolicyAgent(
        learning_rate=0.12,
        discount_factor=0.92,
        exploration_rate=1.0,
        exploration_decay=0.995,
        minimum_exploration=0.03,
        seed=seed,
    )

    environment = EvoCryptEnvironment(seed=seed)

    scenarios = list(
        scenario_names or SCENARIOS.keys()
    )

    episode_rewards = []

    for episode in range(episodes):

        scenario = scenarios[
            episode % len(scenarios)
        ]

        state = environment.reset(
            scenario
        )

        total_reward = 0.0

        while True:

            action = agent.choose_action(
                state,
                explore=True,
            )

            (
                next_state,
                reward,
                done,
                _info,
            ) = environment.step(
                action
            )

            agent.update(
                state,
                action,
                reward,
                next_state,
                done=done,
            )

            total_reward += reward

            state = next_state

            if done:
                break

        agent.episodes += 1
        agent.decay_exploration()

        episode_rewards.append(
            total_reward
        )

    average_reward = (
        sum(episode_rewards)
        /
        max(1, len(episode_rewards))
    )

    return {
        "agent": agent,
        "episodes": episodes,
        "average_reward": round(
            average_reward,
            4,
        ),
        "final_exploration": round(
            agent.exploration_rate,
            5,
        ),
        "states": len(
            agent.q_table
        ),
    }


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Train the EvoCrypt "
            "adaptive security RL policy."
        )
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=3000,
    )

    parser.add_argument(
        "--output",
        default="evocrypt_policy.json",
    )

    args = parser.parse_args()

    result = train_agent(
        episodes=args.episodes
    )

    result["agent"].save(
        args.output
    )

    print(
        "EvoCrypt RL training complete"
    )

    print(
        f"Episodes: {result['episodes']}"
    )

    print(
        f"Average reward: "
        f"{result['average_reward']}"
    )

    print(
        f"States learned: "
        f"{result['states']}"
    )

    print(
        f"Policy saved to: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()