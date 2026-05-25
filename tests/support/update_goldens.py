"""Regenerate all expected.pyi golden files from current generator output.

Usage:
    uv run python -m tests.support.update_goldens
"""

from __future__ import annotations

from pathlib import Path

from stubgen import generate_stub

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "cases" / "libcst"


def main() -> None:
    source_files = sorted(FIXTURES_ROOT.rglob("source.py"))
    updated = 0
    created = 0

    for src_path in source_files:
        expected_path = src_path.with_name("expected.pyi")
        existed = expected_path.exists()

        source_text = src_path.read_text(encoding="utf-8")
        stub = generate_stub(source_text)

        if existed:
            if expected_path.read_text(encoding="utf-8") == stub:
                continue
            updated += 1
        else:
            created += 1

        expected_path.write_text(stub, encoding="utf-8")
        tag = "[CREATED]" if not existed else "[UPDATED]"
        print(f"{tag} {expected_path.relative_to(FIXTURES_ROOT)}")

    total = updated + created
    print(f"\nDone. {total} file{'s' if total != 1 else ''} written ({updated} updated, {created} created).")


if __name__ == "__main__":
    main()
