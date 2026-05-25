from __future__ import annotations
from functools import singledispatch


@singledispatch
def process(value: object) -> str: ...


@process.register
def _process_int(value: int) -> str: ...


@process.register
def _process_str(value: str) -> str: ...
