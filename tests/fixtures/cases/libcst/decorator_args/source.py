from typing import TypeVar

T = TypeVar("T")


def register(name: str) -> object: ...


@register("my_func")
def my_func() -> None: ...


@register("my_class")
class MyClass:
    def method(self) -> int: ...
