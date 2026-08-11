import pytest

from evocrypt.trust import TrustScorer


# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def scorer():
    return TrustScorer(
        low_threshold=40,
        critical_threshold=20
    )


# ============================================================
# SCORE CLAMPING
# ============================================================

def test_score_is_clamped_to_0_100(
    scorer
):

    result = scorer.evaluate(
        signals={},
        previous_score=150,
        context={}
    )

    assert 0 <= result["score"] <= 100


# ============================================================
# NORMAL BEHAVIOR
# ============================================================

def test_normal_behavior_keeps_high_trust(
    scorer
):

    result = scorer.evaluate(

        signals={
            "typing_speed": 5,
            "avg_key_hold": 100,
            "mouse_speed": 250,
            "mouse_distance": 1000,
            "click_count": 10,
            "scroll_distance": 200,
            "idle_time": 2
        },

        previous_score=88,

        context={}
    )

    assert result["score"] <= 88

    assert result["score"] >= 80

    assert result["status"] == "LOW"


# ============================================================
# UNUSUAL TYPING
# ============================================================

def test_unusual_typing_reduces_trust(
    scorer
):

    result = scorer.evaluate(

        signals={
            "typing_speed": 100,
            "avg_key_hold": 10
        },

        previous_score=88,

        context={}
    )

    assert result["score"] < 88

    assert (
        "Unusual typing cadence"
        in result["reasons"]
    )

    assert (
        "Unusual key-hold duration"
        in result["reasons"]
    )


# ============================================================
# SUSPICIOUS BEHAVIOR
# ============================================================

def test_suspicious_behavior_has_large_penalty(
    scorer
):

    result = scorer.evaluate(

        signals={
            "suspicious": True
        },

        previous_score=88,

        context={}
    )

    assert result["penalty"] >= 25

    assert result["score"] < 88

    assert (
        "Suspicious behavior flag"
        in result["reasons"]
    )


# ============================================================
# DEVICE CHANGE
# ============================================================

def test_device_change_reduces_trust(
    scorer
):

    result = scorer.evaluate(

        signals={},

        previous_score=88,

        context={
            "device_changed": True
        }
    )

    assert result["score"] < 88

    assert (
        "Device context changed"
        in result["reasons"]
    )


# ============================================================
# IP CHANGE
# ============================================================

def test_ip_change_reduces_trust(
    scorer
):

    result = scorer.evaluate(

        signals={},

        previous_score=88,

        context={
            "ip_changed": True
        }
    )

    assert result["score"] < 88

    assert (
        "Network context changed"
        in result["reasons"]
    )


# ============================================================
# MULTIPLE ANOMALIES
# ============================================================

def test_multiple_context_anomalies(
    scorer
):

    result = scorer.evaluate(

        signals={},

        previous_score=88,

        context={

            "ip_changed": True,

            "device_changed": True,

            "location_changed": True,

            "unusual_time": True
        }
    )

    assert result["score"] < 88

    assert (
        "Multiple contextual anomalies detected"
        in result["reasons"]
    )


# ============================================================
# RISK CLASSIFICATION
# ============================================================

@pytest.mark.parametrize(

    "score, expected",

    [

        (90, "LOW"),

        (70, "LOW"),

        (69, "MEDIUM"),

        (40, "MEDIUM"),

        (39, "HIGH"),

        (20, "HIGH"),

        (19, "CRITICAL"),

        (0, "CRITICAL")

    ]
)

def test_risk_classification(
    scorer,
    score,
    expected
):

    result = scorer.calculate_risk(
        score
    )

    assert (
        result["risk_level"]
        == expected
    )


# ============================================================
# TRUST RECOVERY
# ============================================================

def test_trust_recovery(
    scorer
):

    recovered = scorer.recover(
        50,
        recovery_rate=5
    )

    assert recovered == 55


def test_trust_recovery_cannot_exceed_100(
    scorer
):

    recovered = scorer.recover(
        98,
        recovery_rate=10
    )

    assert recovered == 100


# ============================================================
# EXPLANATION
# ============================================================

def test_explain_returns_human_readable_text(
    scorer
):

    result = scorer.evaluate(

        signals={
            "suspicious": True
        },

        previous_score=88,

        context={}
    )

    explanation = scorer.explain(
        result
    )

    assert isinstance(
        explanation,
        str
    )

    assert "Trust score" in explanation

    assert "Risk level" in explanation