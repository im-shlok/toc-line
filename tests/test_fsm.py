import csv
import tempfile
import unittest
from itertools import product
from pathlib import Path

from fsm.mealy_machine import MealyMachine
from fsm.moore_machine import MooreMachine
from fsm.simulator import Simulator
from models.gate_input import GateInput as I
from models.gate_state import GateState as S


class FSMTests(unittest.TestCase):
    # Independent expectations from the specification, not imported tables.
    expected_states = {
        S.LOCKED: [S.UNLOCKED, S.LOCKED, S.ALARM, S.ALARM, S.LOCKED],
        S.UNLOCKED: [S.UNLOCKED, S.UNLOCKED, S.LOCKED, S.ALARM, S.UNLOCKED],
        S.ALARM: [S.ALARM, S.ALARM, S.ALARM, S.ALARM, S.LOCKED],
    }
    expected_messages = {
        S.LOCKED: ["Access Granted", "Access Denied", "Unauthorized Access Alarm",
                   "Tailgating Alarm", "No Alarm to Reset"],
        S.UNLOCKED: ["Gate Already Open", "Invalid Scan Ignored", "Passenger Entry Confirmed",
                     "Tailgating Alarm", "No Alarm to Reset"],
        S.ALARM: ["Access Blocked", "Access Blocked", "Alarm Continues",
                  "Alarm Continues", "Alarm Reset"],
    }

    def test_all_30_transitions(self):
        for machine_class, state in product((MooreMachine, MealyMachine), S):
            for index, gate_input in enumerate(I):
                with self.subTest(mode=machine_class.mode, state=state, input=gate_input):
                    result = machine_class(state).process(gate_input)
                    self.assertEqual(result.current, self.expected_states[state][index])
                    self.assertEqual(result.previous, state)
                    self.assertEqual(result.hardware.gate, "Open" if result.current == S.UNLOCKED else "Closed")
                    self.assertEqual(result.hardware.alarm, result.current == S.ALARM)

    def test_all_15_mealy_outputs(self):
        for state in S:
            for index, gate_input in enumerate(I):
                with self.subTest(state=state, input=gate_input):
                    result = MealyMachine(state).process(gate_input)
                    self.assertEqual(result.output, self.expected_messages[state][index])

    def test_moore_outputs_are_only_state_based(self):
        expected = {S.LOCKED: ("Closed", "Red", False),
                    S.UNLOCKED: ("Open", "Green", False), S.ALARM: ("Closed", "Red", True)}
        for state in S:
            output = MooreMachine.output(state)
            self.assertEqual((output.gate, output.indicator, output.alarm), expected[state])
            for gate_input in I:
                result = MooreMachine(state).process(gate_input)
                self.assertEqual(result.output, MooreMachine.output(result.current).message)

    def test_successful_entry_in_both_modes(self):
        for mode in ("Moore", "Mealy"):
            session = Simulator(mode)
            session.process(I.VALID_CARD)
            self.assertEqual(session.state, S.UNLOCKED)
            session.process(I.PUSH_GATE)
            self.assertEqual(session.state, S.LOCKED)
            self.assertEqual(session.entries, 1)
            self.assertEqual(session.alarm_events, 0)

    def test_alarm_is_latched_until_authorized_reset(self):
        for mode in ("Moore", "Mealy"):
            session = Simulator(mode)
            session.process(I.PUSH_GATE)
            for gate_input in (I.VALID_CARD, I.INVALID_CARD, I.PUSH_GATE, I.TAILGATE_DETECTED):
                session.process(gate_input)
                self.assertEqual(session.state, S.ALARM)
                self.assertTrue(session.hardware.alarm)
            self.assertEqual(session.alarm_events, 1)
            session.process(I.AUTHORIZED_RESET)
            self.assertEqual(session.state, S.LOCKED)

    def test_mode_switch_preserves_alarm_and_history(self):
        session = Simulator()
        session.process(I.TAILGATE_DETECTED)
        for mode in ("Mealy", "Moore"):
            session.switch_mode(mode)
            self.assertEqual(session.state, S.ALARM)
            session.process(I.VALID_CARD)
            self.assertEqual(session.state, S.ALARM)
        self.assertEqual(len(session.history), 3)
        self.assertEqual(len(session.events), 6)

    def test_invalid_input_does_not_mutate_state(self):
        for machine_class in (MooreMachine, MealyMachine):
            machine = machine_class(S.UNLOCKED)
            with self.assertRaises(ValueError):
                machine.process("UNKNOWN")
            self.assertEqual(machine.state, S.UNLOCKED)
        with self.assertRaises(ValueError):
            Simulator("invalid")

    def test_export_preserves_transitions_and_mode_events(self):
        session = Simulator()
        session.process(I.VALID_CARD)
        session.switch_mode("Mealy")
        session.process(I.PUSH_GATE)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.csv"
            session.export_csv(path)
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]["next_state"], "UNLOCKED")
        self.assertEqual(rows[3]["output"], "Passenger Entry Confirmed")


if __name__ == "__main__":
    unittest.main()
