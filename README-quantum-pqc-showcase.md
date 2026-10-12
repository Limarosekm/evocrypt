# EvoCrypt Quantum Attack + Post-Quantum Defense Showcase

This is a small additive patch. It does not modify the existing Shor circuit,
crypto provider, key manager, dashboard, or existing tests.

## Install prerequisites

Use the existing EvoCrypt virtual environment. The project should already have
Qiskit, IBM Runtime, `pqcrypto`, and `cryptography` installed.

## Run on real IBM Quantum hardware

From `D:\evocrypt`:

```powershell
python -m evocrypt.quantum.quantum_vs_pqc_demo --backend ibm --shots 1024
```

The command first runs the existing `evocrypt.quantum.shor_rsa_demo` on IBM
hardware, then runs the ML-KEM-768 + HKDF-SHA256 + AES-256-GCM demonstration.

For a local software run:

```powershell
python -m evocrypt.quantum.quantum_vs_pqc_demo --backend simulator --shots 1024
```

## What it demonstrates

1. Shor order-finding on the project's existing toy RSA modulus `N=15`.
2. Post-quantum key establishment with ML-KEM-768.
3. Message encryption/authentication with AES-256-GCM.
4. Rejection of a tampered ciphertext.

## Scientific limitation

The IBM run factors only a tiny, educational RSA instance. It does not break
RSA-2048 or other modern RSA key sizes. ML-KEM-768 is a key-encapsulation
mechanism, not a direct message-encryption algorithm. This showcase runs the
attack and defense sequentially; it does not imply the Shor circuit attacks
the AES key or that the main dashboard already switches algorithms.
