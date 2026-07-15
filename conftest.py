"""Put the eval/ and src/ modules on the import path for tests.

Keeps the module files themselves flat (`from pass_at_k import ...`) instead of
forcing a package layout this early. Revisit if the repo grows.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
for sub in ("eval", "src"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)
