from __future__ import annotations

class Circle:
    @property
    def radius(self) -> float: ...

    @radius.setter
    def radius(self, value: float) -> None: ...

    @staticmethod
    def create() -> "Circle": ...

    @classmethod
    def default(cls) -> "Circle": ...
