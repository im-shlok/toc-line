from dataclasses import dataclass
from datetime import datetime

from models.gate_input import GateInput
from models.gate_output import GateOutput
from models.gate_state import GateState

S = GateState
I = GateInput

# All 15 state/input pairs from the project specification.
TRANSITIONS = {
    S.LOCKED: {
        I.VALID_CARD: S.UNLOCKED, I.INVALID_CARD: S.LOCKED,
        I.PUSH_GATE: S.ALARM, I.TAILGATE_DETECTED: S.ALARM,
        I.AUTHORIZED_RESET: S.LOCKED,
    },
    S.UNLOCKED: {
        I.VALID_CARD: S.UNLOCKED, I.INVALID_CARD: S.UNLOCKED,
        I.PUSH_GATE: S.LOCKED, I.TAILGATE_DETECTED: S.ALARM,
        I.AUTHORIZED_RESET: S.UNLOCKED,
    },
    S.ALARM: {
        I.VALID_CARD: S.ALARM, I.INVALID_CARD: S.ALARM,
        I.PUSH_GATE: S.ALARM, I.TAILGATE_DETECTED: S.ALARM,
        I.AUTHORIZED_RESET: S.LOCKED,
    },
}

STATE_OUTPUTS = {
    S.LOCKED: GateOutput("Closed", "Red", False),
    S.UNLOCKED: GateOutput("Open", "Green", False),
    S.ALARM: GateOutput("Closed", "Red", True),
}


def next_state(state: GateState, gate_input: GateInput) -> GateState:
    return TRANSITIONS[GateState(state)][GateInput(gate_input)]


@dataclass(frozen=True)
class Transition:
    mode: str
    previous: GateState
    input: GateInput
    current: GateState
    output: str
    hardware: GateOutput
    timestamp: datetime

    @property
    def entry_confirmed(self) -> bool:
        return self.previous == S.UNLOCKED and self.input == I.PUSH_GATE
