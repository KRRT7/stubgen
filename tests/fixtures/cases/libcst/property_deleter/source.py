class Circle:
    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value

    @radius.deleter
    def radius(self) -> None:
        del self._radius
