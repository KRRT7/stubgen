from enum import Enum, auto


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
