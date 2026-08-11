import pytest

from evocrypt.session import (
    SessionManager
)


# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def manager():

    return SessionManager(
        timeout_seconds=1800
    )


# ============================================================
# CREATE SESSION
# ============================================================

def test_create_session(
    manager
):

    session = manager.create(

        session_id="session-001",

        user_id="alice"
    )

    assert (
        session.session_id
        == "session-001"
    )

    assert (
        session.user_id
        == "alice"
    )

    assert session.active


# ============================================================
# GET SESSION
# ============================================================

def test_get_session(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    session = manager.get(
        "session-001"
    )

    assert session is not None

    assert (
        session.user_id
        == "alice"
    )


# ============================================================
# UNKNOWN SESSION
# ============================================================

def test_unknown_session_returns_none(
    manager
):

    assert (
        manager.get(
            "does-not-exist"
        )
        is None
    )


# ============================================================
# REQUIRE UNKNOWN SESSION
# ============================================================

def test_require_unknown_session_raises(
    manager
):

    with pytest.raises(
        KeyError
    ):

        manager.require(
            "missing"
        )


# ============================================================
# VALIDATION
# ============================================================

def test_session_is_valid_after_creation(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    assert manager.validate(
        "session-001"
    )


# ============================================================
# TOUCH
# ============================================================

def test_touch_updates_activity(
    manager
):

    session = manager.create(
        "session-001",
        "alice"
    )

    old_activity = (
        session.last_activity
    )

    manager.touch(
        "session-001"
    )

    new_activity = (
        session.last_activity
    )

    assert (
        new_activity
        >= old_activity
    )


# ============================================================
# SESSION AGE
# ============================================================

def test_session_age_is_non_negative(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    age = manager.age_seconds(
        "session-001"
    )

    assert age >= 0


# ============================================================
# IDLE TIME
# ============================================================

def test_idle_time_is_non_negative(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    idle = manager.idle_seconds(
        "session-001"
    )

    assert idle >= 0


# ============================================================
# TERMINATE
# ============================================================

def test_terminate_session(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    result = manager.terminate(

        "session-001",

        reason="Security policy"
    )

    assert result is True

    assert not manager.validate(
        "session-001"
    )


# ============================================================
# TERMINATION REASON
# ============================================================

def test_termination_reason(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    manager.terminate(

        "session-001",

        reason="Critical trust score"
    )

    status = manager.status(
        "session-001"
    )

    assert (
        status["termination_reason"]
        == "Critical trust score"
    )


# ============================================================
# REMOVE SESSION
# ============================================================

def test_remove_session(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    assert manager.remove(
        "session-001"
    )

    assert (
        manager.get(
            "session-001"
        )
        is None
    )


# ============================================================
# METADATA
# ============================================================

def test_session_metadata(
    manager
):

    manager.create(

        "session-001",

        "alice",

        metadata={
            "device": "desktop",
            "browser": "Chrome"
        }
    )

    session = manager.get(
        "session-001"
    )

    assert (
        session.metadata["device"]
        == "desktop"
    )

    assert (
        session.metadata["browser"]
        == "Chrome"
    )


# ============================================================
# UPDATE METADATA
# ============================================================

def test_update_metadata(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    manager.update_metadata(

        "session-001",

        {
            "ip": "127.0.0.1",
            "device": "laptop"
        }
    )

    session = manager.get(
        "session-001"
    )

    assert (
        session.metadata["ip"]
        == "127.0.0.1"
    )

    assert (
        session.metadata["device"]
        == "laptop"
    )


# ============================================================
# ACTIVE SESSION COUNT
# ============================================================

def test_active_session_count(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    manager.create(
        "session-002",
        "bob"
    )

    assert (
        manager.active_count()
        == 2
    )


# ============================================================
# TERMINATED SESSION NOT ACTIVE
# ============================================================

def test_terminated_session_not_active(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    manager.terminate(
        "session-001"
    )

    assert (
        manager.active_count()
        == 0
    )


# ============================================================
# DUPLICATE SESSION
# ============================================================

def test_duplicate_session_rejected(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    with pytest.raises(
        ValueError
    ):

        manager.create(
            "session-001",
            "bob"
        )


# ============================================================
# INVALID SESSION CREATION
# ============================================================

def test_empty_session_id_rejected(
    manager
):

    with pytest.raises(
        ValueError
    ):

        manager.create(
            "",
            "alice"
        )


def test_empty_user_id_rejected(
    manager
):

    with pytest.raises(
        ValueError
    ):

        manager.create(
            "session-001",
            ""
        )


# ============================================================
# CLEANUP
# ============================================================

def test_cleanup_expired_returns_count(
    manager
):

    manager.create(
        "session-001",
        "alice"
    )

    manager.create(
        "session-002",
        "bob"
    )

    count = manager.cleanup_expired()

    assert isinstance(
        count,
        int
    )