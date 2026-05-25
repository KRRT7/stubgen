from typing import Literal


Mode = Literal["r", "w", "a"]


def open(mode: Literal["r", "w"]) -> None: ...
