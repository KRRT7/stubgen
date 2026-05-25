class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class Immutable:
    __slots__ = ("value",)

    def get_value(self) -> int:
        return self.value
