from typing import Generator
from contextlib import contextmanager


@contextmanager
def managed(name: str) -> Generator[None, None, None]:
    print("enter")
    yield
    print("exit")


@contextmanager
def read_file(path: str) -> Generator[str, None, None]:
    f = open(path)
    yield f.read()
    f.close()
