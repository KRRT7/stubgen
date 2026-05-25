from __future__ import annotations
from typing import TypeVar, Generic


T = TypeVar("T", bound=int)


class Box(Generic[T]):
    def get(self) -> T: ...
