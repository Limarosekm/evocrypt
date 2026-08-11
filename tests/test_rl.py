import pytest

from evocrypt.rl import AdaptivePolicyAgent


# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def agent():

    return AdaptivePolicyAgent(
        learning_rate=0.1,
        discount_factor=0.9,
        exploration_rate=0.0
    )


# ============================================================
# TRUST → STATE
# ============================================================

@pytest.mark.parametrize(

    "score, expected_state",

    [

        (100, "HIGH"),

        (90, "HIGH"),

        (70, "HIGH"),

        (69, "MEDIUM"),

        (50, "MEDIUM"),

        (40, "MEDIUM"),

        (39, "LOW"),

        (25, "LOW"),

        (20, "LOW"),

        (19, "VERY_LOW"),

        (0, "VERY_LOW")

    ]
)

def test_state_from_trust(
    agent,
    score,
    expected_state
):

    assert (
        agent.state_from_trust(score)
        == expected_state
    )


# ============================================================
# ACTION LIST
# ============================================================

def test_action_list_exists(
    agent
):

    assert "NORMAL" in agent.ACTIONS

    assert "MONITOR" in agent.ACTIONS

    assert "ROTATE_KEY" in agent.ACTIONS

    assert "REAUTHENTICATE" in agent.ACTIONS

    assert "HYBRID_PQC" in agent.ACTIONS

    assert "TERMINATE_SESSION" in agent.ACTIONS


# ============================================================
# Q TABLE
# ============================================================

def test_q_table_contains_all_states(
    agent
):

    for state in agent.STATES:

        assert state in agent.q_table

        for action in agent.ACTIONS:

            assert action in agent.q_table[state]

            assert (
                agent.q_table[state][action]
                == 0
            )


# ============================================================
# ACTION SELECTION
# ============================================================

def test_choose_action_returns_valid_action(
    agent
):

    action = agent.choose_action(
        "HIGH",
        explore=False
    )

    assert action in agent.ACTIONS


# ============================================================
# Q VALUE UPDATE
# ============================================================

def test_q_value_update(
    agent
):

    old_value = agent.q_table[
        "HIGH"
    ][
        "MONITOR"
    ]

    new_value = agent.update(

        state="HIGH",

        action="MONITOR",

        reward=10,

        next_state="HIGH"
    )

    assert new_value > old_value

    assert (
        agent.q_table["HIGH"]["MONITOR"]
        == new_value
    )


# ============================================================
# NEGATIVE REWARD
# ============================================================

def test_negative_reward_reduces_policy_value(
    agent
):

    agent.set_q_value(
        "LOW",
        "NORMAL",
        10
    )

    value = agent.update(

        state="LOW",

        action="NORMAL",

        reward=-20,

        next_state="VERY_LOW",

        done=True
    )

    assert value < 10


# ============================================================
# DONE STATE
# ============================================================

def test_terminal_update(
    agent
):

    value = agent.update(

        state="VERY_LOW",

        action="TERMINATE_SESSION",

        reward=20,

        next_state="VERY_LOW",

        done=True
    )

    assert value > 0


# ============================================================
# TRAINING EPISODE
# ============================================================

def test_train_episode(
    agent
):

    transitions = [

        {
            "state": "HIGH",

            "action": "MONITOR",

            "reward": 5,

            "next_state": "HIGH"
        },

        {
            "state": "MEDIUM",

            "action": "ROTATE_KEY",

            "reward": 8,

            "next_state": "LOW"
        },

        {
            "state": "LOW",

            "action": "HYBRID_PQC",

            "reward": 12,

            "next_state": "LOW"
        },

        {
            "state": "VERY_LOW",

            "action": "TERMINATE_SESSION",

            "reward": 20,

            "next_state": "VERY_LOW",

            "done": True
        }

    ]

    result = agent.train_episode(
        transitions
    )

    assert result["steps"] == 4

    assert result["total_reward"] == 45

    assert agent.training_steps == 4


# ============================================================
# POLICY
# ============================================================

def test_policy_contains_every_state(
    agent
):

    policy = agent.get_policy()

    for state in agent.STATES:

        assert state in policy

        assert (
            policy[state]
            in agent.ACTIONS
        )


# ============================================================
# SAFETY BOUNDARY
# ============================================================

def test_very_low_trust_forces_termination(
    agent
):

    action = agent.safe_action(

        trust_score=10,

        selected_action="NORMAL"
    )

    assert (
        action
        == "TERMINATE_SESSION"
    )


def test_low_trust_does_not_allow_normal(
    agent
):

    action = agent.safe_action(

        trust_score=30,

        selected_action="NORMAL"
    )

    assert (
        action
        == "HYBRID_PQC"
    )


def test_medium_trust_does_not_allow_normal(
    agent
):

    action = agent.safe_action(

        trust_score=50,

        selected_action="NORMAL"
    )

    assert (
        action
        == "MONITOR"
    )


# ============================================================
# Q TABLE EXPORT
# ============================================================

def test_q_table_export(
    agent
):

    exported = (
        agent.export_q_table()
    )

    assert (
        "q_table"
        in exported
    )

    assert (
        "learning_rate"
        in exported
    )

    assert (
        "discount_factor"
        in exported
    )

    assert (
        "training_steps"
        in exported
    )


# ============================================================
# RESET
# ============================================================

def test_agent_reset(
    agent
):

    agent.update(

        "HIGH",

        "MONITOR",

        10,

        "HIGH"
    )

    assert (
        agent.training_steps
        == 1
    )

    agent.reset()

    assert (
        agent.training_steps
        == 0
    )

    assert (
        agent.q_table["HIGH"]["MONITOR"]
        == 0
    )