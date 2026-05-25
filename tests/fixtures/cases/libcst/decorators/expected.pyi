from __future__ import annotations
import contextlib
import dataclasses
import typing
from typing import Any


def traced(name: str) -> Any: ...


@typing.overload
def parse(value: int) -> int: ...


@typing.overload
def parse(value: str) -> str: ...


@contextlib.contextmanager
def managed() -> typing.Generator[int, None, None]: ...


@traced("top")
def decorated_call(value: int) -> int: ...


@dataclasses.dataclass
class Model:
    name: str


class Example:
    @property
    def name(self) -> str: ...

    @contextlib.contextmanager
    def managed(self) -> typing.Generator[int, None, None]: ...

    @traced("method")
    def decorated_method(self, value: int) -> int: ...
