class Outer:
    class Inner:
        def inner_method(self) -> str:
            return "inner"

    def outer_method(self) -> int:
        return 0


class Top:
    class Middle:
        class Bottom:
            def deep(self) -> None: ...
