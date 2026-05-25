from __future__ import annotations
from typing import Generator, Iterator


def count(n: int) -> Iterator[int]: ...


def infinite() -> Generator[int, None, None]: ...


def delegator() -> Iterator[int]: ...
