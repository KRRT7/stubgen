from __future__ import annotations
from typing import final


@final
class Base:
    def method(self) -> int: ...


class Derived(Base):
    ...


class Service:
    @final
    def handle(self) -> None: ...
