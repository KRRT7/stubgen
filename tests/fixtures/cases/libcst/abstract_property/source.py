import abc


class Base(abc.ABC):
    @abc.abstractproperty
    def value(self) -> int:
        return 0

    @abc.abstractmethod
    def run(self) -> None:
        pass
