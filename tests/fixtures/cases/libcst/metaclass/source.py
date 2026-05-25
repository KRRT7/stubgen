from typing import Type


class Meta(type):
    pass


class MyClass(metaclass=Meta):
    pass


class Configured(metaclass=Meta):
    def method(self) -> int:
        return 1
