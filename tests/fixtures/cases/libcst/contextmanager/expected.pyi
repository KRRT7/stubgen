from __future__ import annotations
from typing import Generator
from contextlib import contextmanager


@contextmanager
def managed(name: str) -> Generator[None, None, None]: ...


@contextmanager
def read_file(path: str) -> Generator[str, None, None]: ...
