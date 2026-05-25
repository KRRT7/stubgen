from __future__ import annotations
from typing import Protocol


class Drawable(Protocol):
    def draw(self) -> None: ...
