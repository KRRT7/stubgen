class Circle:
    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value

    @staticmethod
    def create() -> "Circle":
        return Circle(0)

    @classmethod
    def default(cls) -> "Circle":
        return cls(1)
