from datetime import datetime

from fsm.transition_manager import STATE_OUTPUTS, Transition, next_state
from models.gate_input import GateInput
from models.gate_state import GateState

S = GateState
I = GateInput

MEALY_OUTPUTS = {
    S.LOCKED: {
        I.VALID_CARD: "Access Granted", I.INVALID_CARD: "Access Denied",
        I.PUSH_GATE: "Unauthorized Access Alarm", I.TAILGATE_DETECTED: "Tailgating Alarm",
        I.AUTHORIZED_RESET: "No Alarm to Reset",
    },
    S.UNLOCKED: {
        I.VALID_CARD: "Gate Already Open", I.INVALID_CARD: "Invalid Scan Ignored",
        I.PUSH_GATE: "Passenger Entry Confirmed", I.TAILGATE_DETECTED: "Tailgating Alarm",
        I.AUTHORIZED_RESET: "No Alarm to Reset",
    },
    S.ALARM: {
        I.VALID_CARD: "Access Blocked", I.INVALID_CARD: "Access Blocked",
        I.PUSH_GATE: "Alarm Continues", I.TAILGATE_DETECTED: "Alarm Continues",
        I.AUTHORIZED_RESET: "Alarm Reset",
    },
}


class MealyMachine:
    """Output lambda(q, x) is evaluated BEFORE updating the current state."""

    mode = "Mealy"

    def __init__(self, state: GateState = GateState.LOCKED):
        self.state = GateState(state)

    @staticmethod
    def output(state: GateState, gate_input: GateInput) -> str:
        return MEALY_OUTPUTS[GateState(state)][GateInput(gate_input)]

    def process(self, gate_input: GateInput) -> Transition:
        gate_input = GateInput(gate_input)
        previous = self.state
        message = self.output(previous, gate_input)
        self.state = next_state(previous, gate_input)
        return Transition(self.mode, previous, gate_input, self.state, message,
                          STATE_OUTPUTS[self.state], datetime.now().astimezone())
