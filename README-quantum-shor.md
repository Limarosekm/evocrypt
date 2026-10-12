# EvoCrypt: Shor's algorithm toy RSA attack

This feature is deliberately isolated from EvoCrypt's existing crypto, policy,
and reinforcement-learning modules.

## What it does

1. Builds an 8-control / 4-target quantum phase-estimation circuit for order
   finding with N=15 and a=2.
2. Uses controlled modular multiplication by 2 and 4, followed by inverse QFT.
3. Runs on IBM Quantum hardware first in `auto` mode, or on Qiskit Aer.
4. Uses continued fractions and classical number theory to try to recover 3
   and 5 from measurement results.
5. Uses the recovered factors to derive a toy RSA private exponent and decrypt
   a test message.

The circuit is intentionally specialized to N=15. It is not a scalable attack
against RSA-2048, and textbook RSA in this file is not secure or suitable for
real data.

## Install (Windows PowerShell, from the EvoCrypt root)

```powershell
python -m pip install -r .\requirements-quantum.txt
```

## Configure IBM Quantum credentials

Create an API key and find your service instance/CRN in the IBM Quantum Platform.
Do not share the token or commit it to Git. In an activated virtual environment,
run Python:

```powershell
python
```

Then enter (replace placeholders locally; do not paste your token into chat):

```python
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token="YOUR_API_KEY",
    instance="YOUR_INSTANCE_CRN",
    set_as_default=True,
    overwrite=True,
)
exit()
```

If your account setup does not provide an instance CRN, follow the current IBM
Quantum account setup documentation for the configuration supported by your
account. Account access and backend availability are controlled by IBM.

Optional backend selection:

```powershell
$env:EVOCrypt_IBM_BACKEND = "YOUR_BACKEND_NAME"
```

Leave the variable unset to let the program select a least-busy operational
non-simulator backend with at least 12 qubits.

## Run

From `D:\evocrypt` with the project virtual environment activated:

```powershell
python -m evocrypt.quantum.shor_rsa_demo --backend auto --shots 1024
```

Require real hardware and do not fall back to simulation:

```powershell
python -m evocrypt.quantum.shor_rsa_demo --backend ibm --shots 1024
```

Local simulator only:

```powershell
python -m evocrypt.quantum.shor_rsa_demo --backend simulator --shots 1024
```

Run tests:

```powershell
python -m pytest .\tests\test_shor_rsa_demo.py -q
python -m pytest -q
```

## Interpreting results

- If the result says `Factor recovery source: IBM Quantum hardware measurements`,
  the reported factors were extracted from the IBM job's measurement counts.
- If `auto` mode says simulator fallback was used, the program may have submitted
  a hardware job, but it did not recover factors from the observed hardware counts.
  Do not report that as a successful hardware factorization.
- Hardware is noisy and outcomes are probabilistic. More shots or repeated jobs
  may be required.
- This small-number demonstration explains the mathematical risk Shor's
  algorithm poses to RSA; it does not mean current hardware can factor modern
  RSA key sizes.
