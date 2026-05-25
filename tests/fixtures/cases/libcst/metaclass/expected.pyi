from __future__ import annotations


class Meta(type):
    ...


class MyClass(metaclass=Meta):
    ...


class Configured(metaclass=Meta):
    def method(self) -> int: ...
