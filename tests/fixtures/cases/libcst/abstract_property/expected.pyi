from __future__ import annotations
import abc


class Base(abc.ABC):
    @abc.abstractproperty
    def value(self) -> int: ...

    @abc.abstractmethod
    def run(self) -> None: ...
