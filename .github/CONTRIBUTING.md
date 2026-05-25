# Contributing

Thanks for working on `nuitka-stubgen`.

This project is intentionally small. Changes should keep generated stubs deterministic, easy to
inspect, and compatible with the vendored output used by Nuitka.

## Code Of Conduct

This project follows the Code of Conduct in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security Issues

Please follow [SECURITY.md](SECURITY.md) for reporting security issues.

## Where To Ask / Report

- Bugs and concrete problems: open a GitHub issue.
- Feature requests / design questions: open a GitHub discussion (if enabled) or an issue with a
  clear motivating use case.

When reporting a bug, include:

- a minimal input that reproduces the behavior (ideally a new fixture case)
- expected vs. actual output
- Python version and OS

## Development Setup

```bash
git clone https://github.com/Nuitka/Nuitka-Stubgen
cd Nuitka-Stubgen
uv sync
```

### Pre-commit hooks

```bash
uv run prek run
uv run prek install --hook-type pre-commit --hook-type commit-msg
```

## Project structure

```mkdoc
src/nuitka_stubgen/
  cli.py                        # CLI entry point
  generation/
    core.py                     # generate_stub() — libcst pipeline + fallback
    transform.py                # StubTransformer — strips bodies, normalizes
    imports.py                  # StubImportPruner, UsedNamesCollector
    exports.py                  # extract_exported_names from __all__
    validate.py                 # quality checks: body, roundtrip, name parity
    constants.py                # TYPING_MODULES, TYPEVAR_LIKE, etc.
  vendored/stubgen/
    stubgen.py                  # AST-based legacy generator (ships into Nuitka)
    astunparse.py               # ast.unparse shim for Python 3.5–3.8
    six.py                      # compat for astunparse

tests/
  test_generation.py            # libcst fixture tests (golden-file comparison)
  test_generation_units.py      # unit tests for transform/imports/exports/validate
  test_cli.py                   # CLI argument parsing
  test_error_handling.py        # parse-error fallback tests
  test_stubgen_vendored.py      # vendored stubgen tests + production-readiness
  test_corpus_helpers.py        # corpus pipeline unit tests
  test_corpus_packages.py       # installed-package corpus tests (-m corpus)
  fixtures/cases/
    libcst/                     # golden-file fixtures for libcst generator (57 dirs)
      basic/, overloads/, typeddict/, ...
    ast/legacy/                 # golden-file fixtures for vendored AST generator (15 dirs)
      basic/, type_comment_inline/, ...
  support/
    corpus.py                   # collect_sources, check_source, check_stub_text
    update_goldens.py           # regenerate libcst expected.pyi
    check_goldens_stale.py      # CI staleness check

# Two generators

1. **Libcst (3.9+)** — `src/nuitka_stubgen/generation/` uses libcst to produce stubs.
   This is the primary generator. All `tests/fixtures/cases/libcst/` fixtures
   exercise it.

2. **Vendored AST (3.5–3.8)** — `src/nuitka_stubgen/vendored/stubgen/stubgen.py`
   is the file that ships into Nuitka's `inline_copy/stubgen/`. It uses `ast.parse()`
   and handles `# type:` comments. All `tests/fixtures/cases/ast/legacy/` fixtures
   exercise it. Tested on Docker images for 3.5, 3.6, 3.7, 3.8.

## Running tests

```bash
# All non-corpus tests
uv run pytest tests/ --ignore=tests/test_corpus_packages.py

# Specific test files
uv run pytest tests/test_generation.py -v
uv run pytest tests/test_generation_units.py -v
uv run pytest tests/test_stubgen_vendored.py -v

# Corpus tests (generates stubs for real installed packages)
uv run pytest tests/ -m corpus

# Override corpus package list
NUITKA_STUBGEN_CORPUS_PACKAGES=pytest,packaging uv run pytest -m corpus

# Lint and type check
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run ty check .

# Regenerate all libcst golden files
uv run python -m tests.support.update_goldens
```

## Adding a libcst fixture

1. Create a directory under `tests/fixtures/cases/libcst/<name>/`
2. Add `source.py` with the Python source to generate stubs from
3. Regenerate goldens:

   ```bash
   uv run python -m tests.support.update_goldens
   ```

4. Verify:

   ```bash
   uv run pytest tests/test_generation.py -k "<name>" -v
   ```

Keep cases focused on one behavior. If a bug requires several constructs to
reproduce, add the smallest sample that triggers it.

### Example

```python
# tests/fixtures/cases/libcst/my_feature/source.py
from typing import Optional

def greet(name: str, greeting: Optional[str] = None) -> str:
    return f"{greeting or 'Hello'}, {name}!"
```

After `update_goldens`:

```python
# tests/fixtures/cases/libcst/my_feature/expected.pyi
from __future__ import annotations
from typing import Optional

def greet(name: str, greeting: Optional[str] = ...) -> str: ...
```

## Adding a legacy (vendored AST) fixture

1. Create a directory under `tests/fixtures/cases/ast/legacy/<name>/`
2. Add `source.py` with Python 3.5+ compatible source using `# type:` comments
3. Generate `expected.pyi`:

   ```bash
   uv run python -c "
   import sys
   sys.path.insert(0, 'src/nuitka_stubgen/vendored/stubgen')
   import stubgen
   source = open('tests/fixtures/cases/ast/legacy/<name>/source.py').read()
   open('tests/fixtures/cases/ast/legacy/<name>/expected.pyi', 'w').write(
       stubgen.generate_stub_from_source(source, output_file_path=None, text_only=True)
   )
   "
   ```

4. Verify locally and in Docker:

   ```bash
   uv run pytest tests/test_stubgen_vendored.py -v
   docker run --rm -v "$(pwd):/repo" -w /repo python:3.8-slim \
     python tests/run_vendor_py35.py src/nuitka_stubgen/vendored/stubgen tests/fixtures/cases/ast
   ```

## Vendored stubgen in Docker

The vendored AST-based generator is tested on the exact Python versions Nuitka
targets via Docker:

```bash
for ver in 3.5 3.6 3.7 3.8 3.9 3.10 3.11 3.12 3.13 3.14-rc; do
  docker run --rm -v "$(pwd):/repo" -w /repo python:$ver-slim \
    python tests/run_vendor_py35.py src/nuitka_stubgen/vendored/stubgen tests/fixtures/cases/ast
done
```

## Pull Requests

Use the [pull request template](pull_request_template.md) when opening a PR.
Prefer narrowly scoped changes. Refactors are welcome when they remove real
duplication or make generator behavior easier to test.

Pull requests should:

- include a focused description and rationale
- include tests when behavior changes
- keep formatting changes separate from behavior changes

## Commit Messages

Use Conventional Commits:

```bash
uvx --from commitizen cz commit
```

Commitizen is configured with `cz_conventional_commits` in `pyproject.toml`.

## AI Assistance

AI assistance is fine, but please make sure you understand the changes you
submit. If a PR is largely AI-authored, disclose that in the PR description
to help reviewers calibrate scrutiny.
