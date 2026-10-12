from evocrypt.quantum.quantum_vs_pqc_demo import run_pqc_defense


def test_pqc_defense_demo_passes():
    assert run_pqc_defense() is True
