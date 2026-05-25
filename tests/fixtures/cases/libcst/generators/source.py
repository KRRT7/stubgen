from typing import Generator, Iterator


def count(n: int) -> Iterator[int]:
    for i in range(n):
        yield i


def infinite() -> Generator[int, None, None]:
    while True:
        yield 1


def delegator() -> Iterator[int]:
    yield from count(5)
