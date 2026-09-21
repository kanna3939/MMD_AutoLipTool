import sys
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTS_DIR.parent / "src"

for path in (str(SRC_DIR), str(TESTS_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)
