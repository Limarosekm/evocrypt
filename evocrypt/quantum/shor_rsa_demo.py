"""
EvoCrypt: full small-number Shor order-finding circuit for RSA toy modulus N=15.

This is a research/education feature, not a production cryptosystem.
The quantum circuit performs phase estimation using controlled modular
multiplication and an inverse QFT. Classical post-processing estimates the
order, factors N, and demonstrates textbook RSA decryption.

Modes:
  auto       Try IBM Quantum hardware first; fall back to Aer simulator.
  ibm        Require IBM Quantum hardware; do not silently fall back.
  simulator Run locally using Qiskit Aer.
"""

from __future__ import annotations

import argparse
import os
import sys
from fractions import Fraction
from math import gcd
from typing import Mapping, Optional

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator


N = 15
BASE = 2
CONTROL_QUBITS = 8
TARGET_QUBITS = 4
RSA_PUBLIC_EXPONENT = 7
TOY_MESSAGE = 2


def _m2_mod15_gate():
    """Optimized four-qubit permutation for multiplication by 2 mod 15."""
    gate_circuit = QuantumCircuit(4, name="M2_mod15")
    gate_circuit.swap(2, 3)
    gate_circuit.swap(1, 2)
    gate_circuit.swap(0, 1)
    return gate_circuit.to_gate(label="M2")


def _m4_mod15_gate():
    """Optimized four-qubit permutation for multiplication by 4 mod 15."""
    gate_circuit = QuantumCircuit(4, name="M4_mod15")
    gate_circuit.swap(1, 3)
    gate_circuit.swap(0, 2)
    return gate_circuit.to_gate(label="M4")


def build_order_finding_circuit() -> QuantumCircuit:
    """
    Build the full 8-control + 4-target phase-estimation circuit for N=15, a=2.

    For this particular modulus, a^(2^k) mod 15 is 2 for k=0, 4 for k=1,
    and 1 for k>=2. The M2 and M4 gates are explicitly synthesized as SWAP
    networks, as in IBM's published Shor tutorial; this is a small-instance
    construction and does not scale directly to large RSA moduli.
    """
    control = QuantumRegister(CONTROL_QUBITS, name="C")
    target = QuantumRegister(TARGET_QUBITS, name="T")
    output = ClassicalRegister(CONTROL_QUBITS, name="out")
    circuit = QuantumCircuit(control, target, output)

    # Prepare target register |1>.
    circuit.x(target[0])

    m2_controlled = _m2_mod15_gate().control(1)
    m4_controlled = _m4_mod15_gate().control(1)

    for k, qubit in enumerate(control):
        circuit.h(qubit)
        multiplier = pow(BASE, 2**k, N)

        if multiplier == 2:
            circuit.append(m2_controlled, [qubit, *target])
        elif multiplier == 4:
            circuit.append(m4_controlled, [qubit, *target])
        # Multiplier 1 is the identity and requires no gate.

    circuit.compose(
        QFT(CONTROL_QUBITS, inverse=True, do_swaps=True),
        qubits=list(control),
        inplace=True,
    )
    circuit.measure(control, output)
    return circuit


def find_factors_from_counts(
    counts: Mapping[str, int], n: int = N, a: int = BASE
) -> Optional[dict]:
    """
    Use measured phase bitstrings and continued fractions to try to factor n.

    Returns factor/order/measurement details when successful, else None.
    Noise can produce unusable samples, so failure is a valid outcome.
    """
    num_control = CONTROL_QUBITS
    for bitstring, frequency in sorted(
        counts.items(), key=lambda item: item[1], reverse=True
    ):
        normalized = bitstring.replace(" ", "")
        try:
            measured_integer = int(normalized, 2)
        except ValueError:
            continue

        phase = measured_integer / (2**num_control)
        fraction = Fraction(phase).limit_denominator(n)
        denominator = fraction.denominator
        if phase == 0 or denominator <= 1:
            continue

        # A reduced phase k/r may reveal only a divisor of the true order.
        # Check small multiples of the denominator for the actual order.
        order = None
        for candidate in range(denominator, n + 1, denominator):
            if pow(a, candidate, n) == 1:
                order = candidate
                break

        if order is None or order % 2 != 0:
            continue

        x = pow(a, order // 2, n)
        if x in (1, n - 1):
            continue

        factor_a = gcd(x - 1, n)
        factor_b = gcd(x + 1, n)
        for p in (factor_a, factor_b):
            if 1 < p < n and n % p == 0:
                q = n // p
                return {
                    "p": min(p, q),
                    "q": max(p, q),
                    "order": order,
                    "phase": phase,
                    "bitstring": normalized,
                    "frequency": frequency,
                }

    return None


def rsa_toy_round_trip(p: int, q: int, message: int = TOY_MESSAGE) -> dict:
    """
    Derive a toy RSA private exponent from recovered factors and decrypt.

    Textbook RSA is used only to make the attack outcome easy to understand.
    Do not use this function or textbook RSA for real data.
    """
    n = p * q
    phi = (p - 1) * (q - 1)
    e = RSA_PUBLIC_EXPONENT
    if gcd(e, phi) != 1:
        raise ValueError("The chosen public exponent is not coprime to phi(N).")

    d = pow(e, -1, phi)
    ciphertext = pow(message, e, n)
    plaintext = pow(ciphertext, d, n)
    return {
        "n": n,
        "e": e,
        "phi": phi,
        "d": d,
        "message": message,
        "ciphertext": ciphertext,
        "decrypted": plaintext,
        "verified": plaintext == message,
    }


def run_simulator(circuit: QuantumCircuit, shots: int) -> dict:
    """Run the circuit locally using Qiskit Aer."""
    simulator = AerSimulator()
    compiled = transpile(circuit, simulator, optimization_level=1)
    result = simulator.run(compiled, shots=shots).result()
    return {
        "counts": result.get_counts(compiled),
        "backend": "Qiskit Aer simulator",
        "job_id": None,
    }


def run_ibm_hardware(circuit: QuantumCircuit, shots: int) -> dict:
    """
    Submit the circuit to a real IBM Quantum backend.

    Credentials must already be configured with QiskitRuntimeService.save_account
    or available through the Qiskit IBM Runtime account configuration.
    EVOCrypt_IBM_BACKEND can optionally specify a backend name.
    """
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService()
    requested_backend = os.getenv("EVOCrypt_IBM_BACKEND", "").strip()

    if requested_backend:
        backend = service.backend(requested_backend)
        if getattr(backend, "num_qubits", 0) < circuit.num_qubits:
            raise RuntimeError(
                f"Backend {requested_backend} has fewer than "
                f"{circuit.num_qubits} qubits."
            )
    else:
        backend = service.least_busy(
            operational=True,
            simulator=False,
            min_num_qubits=circuit.num_qubits,
        )

    pass_manager = generate_preset_pass_manager(
        optimization_level=2, backend=backend
    )
    isa_circuit = pass_manager.run(circuit)

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)
    result = job.result()[0]
    counts = result.data.out.get_counts()

    return {
        "counts": counts,
        "backend": backend.name,
        "job_id": job.job_id(),
    }


def _print_counts(counts: Mapping[str, int], limit: int = 12) -> None:
    print("\nMost frequent measured control-register bitstrings:")
    for bitstring, frequency in sorted(
        counts.items(), key=lambda item: item[1], reverse=True
    )[:limit]:
        print(f"  {bitstring}: {frequency}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="EvoCrypt Shor RSA toy attack for N=15."
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "ibm", "simulator"),
        default="auto",
        help="auto tries IBM hardware first; simulator runs locally.",
    )
    parser.add_argument(
        "--shots", type=int, default=1024, help="Measurements per quantum job."
    )
    parser.add_argument(
        "--hardware-attempts",
        type=int,
        default=2,
        help="Number of hardware jobs to try before simulator fallback in auto mode.",
    )
    args = parser.parse_args(argv)

    if args.shots < 1:
        parser.error("--shots must be positive")
    if args.hardware_attempts < 1:
        parser.error("--hardware-attempts must be positive")

    circuit = build_order_finding_circuit()
    print("EvoCrypt — Shor order-finding / toy RSA attack")
    print(f"RSA modulus N = {N}; base a = {BASE}")
    print(
        f"Circuit: {circuit.num_qubits} qubits "
        f"({CONTROL_QUBITS} control + {TARGET_QUBITS} target), "
        f"{args.shots} shots per job"
    )
    print("Scope: tiny educational RSA instance only; not RSA-2048.")

    chosen_result = None
    factors = None
    factor_source = None

    if args.backend in ("auto", "ibm"):
        for attempt in range(1, args.hardware_attempts + 1):
            try:
                print(f"\nSubmitting IBM Quantum hardware job {attempt}...")
                hardware_result = run_ibm_hardware(circuit, args.shots)
                print(f"IBM backend: {hardware_result['backend']}")
                print(f"IBM job ID: {hardware_result['job_id']}")
                _print_counts(hardware_result["counts"])
                factors = find_factors_from_counts(hardware_result["counts"])
                if factors:
                    chosen_result = hardware_result
                    factor_source = "IBM Quantum hardware measurements"
                    break
                print("No non-trivial factor extracted from this hardware job.")
            except Exception as exc:
                print(f"IBM hardware execution failed: {type(exc).__name__}: {exc}")
                if args.backend == "ibm":
                    print("Hardware-only mode requested; no simulator fallback.")
                    return 2
                break

        if args.backend == "ibm" and not factors:
            print(
                "Hardware jobs ran, but no factor was recovered. "
                "No simulator result will be substituted in IBM-only mode."
            )
            return 3

    if args.backend == "simulator" or (args.backend == "auto" and not factors):
        if args.backend == "auto":
            print(
                "\nUsing simulator fallback for factor recovery. "
                "Any earlier IBM measurements remain separate above."
            )
        print("\nRunning local Qiskit Aer simulator...")
        chosen_result = run_simulator(circuit, args.shots)
        print(f"Execution source: {chosen_result['backend']}")
        _print_counts(chosen_result["counts"])
        factors = find_factors_from_counts(chosen_result["counts"])
        factor_source = chosen_result["backend"]

    if not factors:
        print("\nNo factor recovered from the available measurements.")
        print("Try more shots, another hardware job, or simulator mode.")
        return 4

    p, q = factors["p"], factors["q"]
    print(f"\nFactor recovery source: {factor_source}")
    print(f"Estimated order r = {factors['order']}")
    print(f"Recovered factors: p = {p}, q = {q}")

    rsa = rsa_toy_round_trip(p, q)
    print("\nToy RSA result (textbook RSA; educational only):")
    print(f"  Public key:  (N={rsa['n']}, e={rsa['e']})")
    print(f"  phi(N):      {rsa['phi']}")
    print(f"  Recovered private exponent d: {rsa['d']}")
    print(f"  Original message:             {rsa['message']}")
    print(f"  Public-key ciphertext:        {rsa['ciphertext']}")
    print(f"  Decrypted message:             {rsa['decrypted']}")
    print(f"  Decryption verified:           {rsa['verified']}")

    if factor_source == "IBM Quantum hardware measurements":
        print("\nRESULT: factors and toy RSA decryption were recovered from IBM hardware data.")
    elif args.backend == "auto":
        print(
            "\nRESULT: the attack completed using simulator measurements. "
            "This run does not establish successful hardware factor recovery."
        )
    else:
        print("\nRESULT: the attack completed using simulator measurements.")

    print(
        "\nScientific limitation: this circuit is specialized to N=15. "
        "It does not demonstrate breaking modern RSA key sizes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
