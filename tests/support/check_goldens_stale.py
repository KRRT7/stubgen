"""Check that all golden files are up-to-date with the current generator output.

Exits with code 1 if any expected.pyi differs from what ``generate_stub``
currently produces.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    updater = subprocess.run(
        [sys.executable, "-m", "tests.support.update_goldens"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    if updater.returncode != 0:
        print("update_goldens failed:", file=sys.stderr)
        print(updater.stderr, file=sys.stderr)
        return 1

    diff_result = subprocess.run(
        ["git", "diff", "--stat", "--", "tests/fixtures/cases/"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    if diff_result.stdout.strip():
        print("Golden files are out of date! Regenerate with:")
        print("  uv run python -m tests.support.update_goldens")
        print()
        print(diff_result.stdout)
        return 1

    print("All golden files are up-to-date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
