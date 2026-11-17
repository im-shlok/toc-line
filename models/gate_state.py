from enum import Enum


class GateState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    ALARM = "ALARM"
