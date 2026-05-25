from __future__ import annotations
from typing import Any

def complex_func(a: Any, b: Any, c: Any=...) -> Any: ...


class Database:

    def __init__(self, host: Any, port: Any) -> None: ...

    async def query(self, sql: Any, params: Any=...) -> Any: ...
