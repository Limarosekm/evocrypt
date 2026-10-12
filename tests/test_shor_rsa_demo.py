"""Tests for the isolated EvoCrypt small-number Shor demonstration."""

from evocrypt.quantum.shor_rsa_demo import (
    build_order_finding_circuit,
    find_factors_from_counts,
    rsa_toy_round_trip,
)


def test_full_order_finding_circuit_shape():
    circuit = build_order_finding_circuit()
    assert circuit.num_qubits == 12
    assert circuit.num_clbits == 8


def test_postprocessing_recovers_factors_from_ideal_phase():
    # 01000000 represents phase 64/256 = 1/4, which reveals order 4 for a=2 mod 15.
    result = find_factors_from_counts({"01000000": 100}, n=15, a=2)
    assert result is not None
    assert (result["p"], result["q"]) == (3, 5)
    assert result["order"] == 4


def test_rsa_toy_decrypts_after_factors_are_known():
    result = rsa_toy_round_trip(3, 5, message=2)
    assert result["n"] == 15
    assert result["phi"] == 8
    assert result["d"] == 7
    assert result["verified"] is True
    assert result["decrypted"] == 2


def test_unhelpful_measurement_does_not_claim_factorization():
    assert find_factors_from_counts({"00000000": 1024}, n=15, a=2) is None
