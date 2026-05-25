from typing import Optional


def f(x: int) -> Optional[int]:
    if (y := x + 1) > 0:
        return y
    return None
