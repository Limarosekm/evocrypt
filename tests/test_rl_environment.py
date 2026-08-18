from evocrypt.rl.environment import (
    EvoCryptEnvironment,
    SCENARIOS,
)


def test_all_scenarios_reset():

    env = EvoCryptEnvironment(
        seed=42
    )

    for name in SCENARIOS:

        state = env.reset(name)

        assert isinstance(
            state,
            str
        )

        assert (
            0
            <= env.trust_score
            <= 100
        )

        assert (
            0
            <= env.threat
            <= 100
        )


def test_trust_never_exceeds_100():

    env = EvoCryptEnvironment(
        seed=42
    )

    env.reset("normal")

    for _ in range(20):

        _, _, done, _ = env.step(
            "NORMAL"
        )

        assert (
            0
            <= env.trust_score
            <= 100
        )

        if done:
            break


def test_combined_attack_is_persistent():

    env = EvoCryptEnvironment(
        seed=42
    )

    env.reset(
        "combined_attack"
    )

    initial = env.threat

    _, _, _, info = env.step(
        "MONITOR"
    )

    assert (
        initial > 70
    )

    assert (
        info["threat"] > 0
    )


def test_recovery_reduces_threat():

    env = EvoCryptEnvironment(
        seed=42
    )

    env.reset("normal")

    env.state.threat = 8

    _, _, _, info = env.step(
        "NORMAL"
    )

    assert (
        info["threat"]
        < 8
    )