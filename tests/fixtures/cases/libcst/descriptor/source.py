from typing import Any


class Descriptor:
    def __get__(self, obj, objtype=None):
        # type: (Any, type) -> int
        return 42

    def __set__(self, obj, value):
        # type: (Any, int) -> None
        pass

    def __delete__(self, obj):
        # type: (Any) -> None
        pass


class MyClass:
    attr = Descriptor()
