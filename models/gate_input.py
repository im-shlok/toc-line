from enum import Enum


class GateInput(str, Enum):
    VALID_CARD = "VALID_CARD"
    INVALID_CARD = "INVALID_CARD"
    PUSH_GATE = "PUSH_GATE"
    TAILGATE_DETECTED = "TAILGATE_DETECTED"
    AUTHORIZED_RESET = "AUTHORIZED_RESET"

    @property
    def label(self) -> str:
        return {
            self.VALID_CARD: "Valid card scanned",
            self.INVALID_CARD: "Invalid card scanned",
            self.PUSH_GATE: "Gate pushed",
            self.TAILGATE_DETECTED: "Tailgate detected",
            self.AUTHORIZED_RESET: "Authorized reset",
        }[self]
