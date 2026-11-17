from datetime import datetime

from fsm.transition_manager import STATE_OUTPUTS, Transition, next_state
from models.gate_input import GateInput
from models.gate_output import GateOutput
from models.gate_state import GateState


class MooreMachine:
    """Output lambda(q) depends only on the state, including at startup."""

    mode = "Moore"

    def __init__(self, state: GateState = GateState.LOCKED):
        self.state = GateState(state)

    @staticmethod
    def output(state: GateState) -> GateOutput:
        return STATE_OUTPUTS[GateState(state)]

    def process(self, gate_input: GateInput) -> Transition:
        gate_input = GateInput(gate_input)
        previous = self.state
        self.state = next_state(previous, gate_input)
        hardware = self.output(self.state)
        return Transition(self.mode, previous, gate_input, self.state,
                          hardware.message, hardware, datetime.now().astimezone())
