from typing import Union


def process(value: object) -> Union[int, str, None]:
    match value:
        case int():
            return value
        case str():
            return value
        case _:
            return None
