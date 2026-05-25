from functools import singledispatch


@singledispatch
def process(value: object) -> str:
    return str(value)


@process.register
def _process_int(value: int) -> str:
    return str(value)


@process.register
def _process_str(value: str) -> str:
    return value
