# stubgen

A deterministic type stub generator for Python packages.

## Overview

`stubgen` generates type stub (`.pyi`) files from Python source using [libcst](https://libcst.readthedocs.io/). It prioritizes:

1. **Deterministic output** — identical stubs on every run for the same source.
2. **Correctness** — preserves type annotations, re-exports, overloads, and `__all__` filtering.
3. **Clean stubs** — strips function bodies, removes unused imports, and emits a `from __future__ import annotations` header.

## Installation

```bash
uv tool install stubgen
# or
pip install stubgen
```

## CLI

Generate a stub alongside the source file:

```bash
stubgen path/to/module.py
```

Write to a specific output path:

```bash
stubgen path/to/module.py -o path/to/module.pyi
```

## Python API

```python
from stubgen import generate_stub, write_stub

stub_text = generate_stub("def add(x: int, y: int) -> int: return x + y\n")
write_stub("path/to/module.py", "path/to/module.pyi")
```

## Requirements

- Python ≥ 3.9
- `libcst ≥ 1.8.6`

## License

MIT
