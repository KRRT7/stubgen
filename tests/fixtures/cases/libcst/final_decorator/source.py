from typing import final


@final
class Base:
    def method(self) -> int:
        return 1


class Derived(Base):
    pass


class Service:
    @final
    def handle(self) -> None:
        pass
