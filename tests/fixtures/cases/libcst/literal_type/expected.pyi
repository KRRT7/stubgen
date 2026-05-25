from __future__ import annotations
from typing import Literal


Mode: Literal["r", "w", "a"]


def open(mode: Literal["r", "w"]) -> None: ...
