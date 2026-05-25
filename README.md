# Nuitka-Stubgen

A deterministic type stub generator for Python packages, designed for use in Nuitka.

## Overview

`nuitka-stubgen` generates type stubs (`.pyi` files) from Python source. It prioritizes:

1. **Deterministic output**: Generating the exact same stub every time for the same source.
2. **Compatibility**: Supporting modern type annotations while remaining robust for legacy codebases.
3. **Vendoring**: Providing a standalone, dependency-free version for Nuitka's `inline_copy`.

The package provides two engines:

- **Modern Engine (library + CLI)**: Uses `libcst` to generate stubs. Requires Python 3.9+.
- **Compatibility Engine (vendored output)**: An AST-based engine that generates a
  Nuitka-vendorable bundle. The generated `stubgen.py` is kept parseable as Python 3.5
  syntax and has no external runtime dependencies beyond the bundled `astunparse` and `six`.

## Features

- **Nuitka Integration**: Automates the generation of `stubgen.py` for Nuitka's `inline_copy`,
  ensuring full Python 3.5 runtime compatibility.
- **Legacy Support**: Extracts types from Python 2/3 style type comments (`# type: int`).
- **Deterministic Output**: Consistent stub generation across multiple runs and Python versions.

## Usage

### Main Tool

Install with `uv` or `pip`:

```bash
uv tool install nuitka-stubgen
```

Generate a stub for a Python source file:

```bash
nuitka-stubgen path/to/module.py
```

Write to a specific output path:

```bash
nuitka-stubgen path/to/module.py -o path/to/module.pyi
```

### Vendoring Tool

The vendoring tool generates a Nuitka-ready bundle:

```bash
nuitka-stubgen-vendor -o stubgen/
```

This produces a `stubgen/` directory containing `stubgen.py`, `astunparse.py`, `six.py`,
and the relevant license file(s).

## Python API

```python
from nuitka_stubgen import generate_stub, write_stub

stub_text = generate_stub("def add(x: int, y: int) -> int: return x + y\n")
write_stub("path/to/module.py", "path/to/module.pyi")
```

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for setup, testing, and adding fixtures.

## License

MIT


## Architecture

Two stub generators exist in this repo:

1. **`/Users/krrt7/Desktop/work/nuitka_org/Nuitka-Stubgen/src/nuitka_stubgen/vendored/`** — static AST-based bundle. This is the    bundle that's
   copies into `Nuitka/build/inline_copy/stubgen/`. It works on Python 3.5 thru 3.14 and
   passes all tests. It is **not generated** — it is maintained directly as the
   canonical source for the AST engine. Do not treat it as a build artifact.
   Nuitka itself tests/Nuitka/nuitka/build/inline_copy/stubgen has it's own importing mechanism so an **init**.py is not needed for it

2. **`src/nuitka_stubgen/generation/`** — the new libcst-based implementation,
   active on Python 3.9+.
