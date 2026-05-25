from __future__ import annotations

class Outer:
    class Inner:
        def inner_method(self) -> str: ...

    def outer_method(self) -> int: ...


class Top:
    class Middle:
        class Bottom:
            def deep(self) -> None: ...
