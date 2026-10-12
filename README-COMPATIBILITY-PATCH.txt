EvoCrypt compatibility patch

Back up your current files before applying. This patch adds the API expected by tests/test_crypto.py while preserving the legacy methods used by AdaptiveCryptoEngine.

Copy the four files under evocrypt/crypto/ into your D:\evocrypt project, overwriting only those four files. Then run:
  python -m pytest .\tests\test_crypto.py -q
  python -m pytest -q

Note: ML-KEM remains unavailable unless a compatible `oqs` provider is installed. The hybrid provider currently reports availability/status; it does not implement ML-DSA signatures or a complete hybrid protocol.
