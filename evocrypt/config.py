from dataclasses import dataclass


@dataclass
class EvoCryptConfig:
    """
    Configuration settings for the EvoCrypt adaptive
    session-security framework.
    """

    # Enable adaptive security decisions
    adaptive: bool = True

    # Enable the PQC mode when a validated PQC provider
    # has been connected.
    pqc_enabled: bool = False

    # Initial trust assigned when a new session starts
    initial_trust: float = 88.0

    # Maximum age of a session key before rotation
    key_rotation_seconds: int = 900

    # Trust score below which the session enters
    # a higher-risk state
    low_trust_threshold: float = 40.0

    # Trust score below which the session is considered
    # critical
    critical_trust_threshold: float = 20.0

    # Whether EvoCrypt is allowed to terminate
    # highly suspicious sessions
    allow_session_termination: bool = True