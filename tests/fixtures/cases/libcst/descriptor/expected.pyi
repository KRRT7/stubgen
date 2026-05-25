from __future__ import annotations
from typing import Any


class Descriptor:
    def __get__(self, obj: Any, objtype: Any=...) -> Any: ...

    def __set__(self, obj: Any, value: Any) -> Any: ...

    def __delete__(self, obj: Any) -> Any: ...


class MyClass:
    ...
