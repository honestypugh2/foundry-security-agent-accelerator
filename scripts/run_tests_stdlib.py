"""Historical presenter command alias; this repository uses installed pytest, not stdlib tests."""

import subprocess
import sys

if __name__ == "__main__":
    print(
        "Compatibility command: running pytest with installed dependencies; "
        "not a standard-library-only test runner.",
        flush=True,
    )
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", *sys.argv[1:]]))
