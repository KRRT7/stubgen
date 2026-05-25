from __future__ import annotations
from typing import Any

windows = {}  # type: dict[str, list[tuple[int, str]]]
casts = []  # type: List[Callable[[int], str]]


def nested() -> Any: ...
