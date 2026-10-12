"""One-command EvoCrypt showcase: real IBM Shor demo + PQC defense.

Run from the repository root:
    python -m evocrypt.quantum.quantum_vs_pqc_demo --backend ibm --shots 1024

The Shor stage delegates to the existing, tested toy-RSA demo. The PQC stage
uses ML-KEM-768 + HKDF-SHA256 + AES-256-GCM. This is an educational showcase,
not a claim of breaking modern RSA key sizes.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from cryptography.exceptions import InvalidTag

from evocrypt.crypto.pqc_hybrid import HybridEnvelope, PQCHybridEncryption


def run_quantum_attack(backend: str, shots: int) -> int:
    """Run EvoCrypt's existing Shor demo and return its process exit code."""
    print("\n" + "=" * 72)
    print("PART 1 — QUANTUM ATTACK: SHOR ORDER-FINDING AGAINST TOY RSA")
    print("=" * 72)
    command = [
        sys.executable,
        "-m",
        "evocrypt.quantum.shor_rsa_demo",
        "--backend",
        backend,
        "--shots",
        str(shots),
    ]
    print("Running the existing Shor demo:", " ".join(command), flush=True)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print("\nQuantum stage did not complete successfully.")
    return result.returncode


def run_pqc_defense() -> bool:
    """Demonstrate post-quantum key establishment and authenticated encryption."""
    print("\n" + "=" * 72)
    print("PART 2 — POST-QUANTUM DEFENSE: ML-KEM-768 + AES-256-GCM")
    print("=" * 72)

    public_key, private_key = PQCHybridEncryption.generate_keypair()
    message = (
        b"EvoCrypt: protecting messages with post-quantum key establishment."
    )
    aad = b"EvoCrypt-quantum-pqc-showcase-v1"

    envelope: HybridEnvelope = PQCHybridEncryption.encrypt(
        public_key, message, associated_data=aad
    )
    recovered = PQCHybridEncryption.decrypt(
        private_key, envelope, associated_data=aad
    )
    round_trip_ok = recovered == message

    print("KEM: ML-KEM-768")
    print(f"Receiver public key: {len(public_key)} bytes")
    print(f"KEM ciphertext:      {len(envelope.kem_ciphertext)} bytes")
    print("Key derivation:      HKDF-SHA256")
    print("Message encryption:  AES-256-GCM")
    print(f"Message round trip:  {'PASS' if round_trip_ok else 'FAIL'}")
    print("Recovered message:   " + recovered.decode("utf-8"))

    # Flip one ciphertext bit. AES-GCM must reject the altered envelope.
    damaged = bytes(
        [envelope.ciphertext[0] ^ 1]
    ) + envelope.ciphertext[1:]
    tamper_rejected = False
    try:
        damaged_envelope = HybridEnvelope(
            kem_ciphertext=envelope.kem_ciphertext,
            salt=envelope.salt,
            nonce=envelope.nonce,
            ciphertext=damaged,
        )
        PQCHybridEncryption.decrypt(
            private_key, damaged_envelope, associated_data=aad
        )
    except InvalidTag:
        tamper_rejected = True

    print(f"Tampering detection: {'PASS' if tamper_rejected else 'FAIL'}")
    print("\nInterpretation:")
    print("- Shor's demo illustrates why RSA is vulnerable in principle.")
    print("- ML-KEM-768 establishes a post-quantum shared secret.")
    print("- AES-GCM protects and authenticates the message.")
    print("- These are complementary demonstrations, not a claim that the")
    print("  hardware run broke modern RSA-2048.")
    return round_trip_ok and tamper_rejected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="EvoCrypt quantum attack and post-quantum defense showcase."
    )
    parser.add_argument(
        "--backend",
        choices=("ibm", "simulator", "auto"),
        default="ibm",
        help="Backend for the existing Shor demo (default: ibm).",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Quantum measurement shots (default: 1024).",
    )
    args = parser.parse_args()

    if args.shots < 1:
        parser.error("--shots must be at least 1")

    attack_code = run_quantum_attack(args.backend, args.shots)
    defense_ok = run_pqc_defense()

    print("\n" + "=" * 72)
    print("EVOCRYPT SHOWCASE SUMMARY")
    print("=" * 72)
    print(f"Quantum demo process: {'PASS' if attack_code == 0 else 'FAILED'}")
    print(f"Post-quantum defense: {'PASS' if defense_ok else 'FAILED'}")
    print("Research scope: real-hardware toy-RSA demonstration + software PQC demo.")
    return 0 if attack_code == 0 and defense_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
