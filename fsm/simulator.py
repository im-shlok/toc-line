"""Session orchestration: mode selection never clears a security alarm."""
import csv
from datetime import datetime
from pathlib import Path

from fsm.mealy_machine import MealyMachine
from fsm.moore_machine import MooreMachine
from fsm.transition_manager import STATE_OUTPUTS, Transition
from models.gate_input import GateInput
from models.gate_state import GateState
from models.metro_card import MetroCard, currency, money


class Simulator:
    def __init__(self, mode: str = "Moore", card: MetroCard | None = None, fare="20.00"):
        if mode not in {"Moore", "Mealy"}:
            raise ValueError("Choose Moore or Mealy")
        self.machine = MooreMachine() if mode == "Moore" else MealyMachine()
        self.card = card if card is not None else MetroCard()
        self.fare = money(fare)
        if self.fare <= 0:
            raise ValueError("Fare must be greater than zero.")
        self.card_message = f"Ready to scan. Demo fare: {currency(self.fare)}."
        self.history: list[Transition] = []
        self.entries = 0
        self.alarm_events = 0
        self.events: list[dict[str, str]] = []
        self.record("System started. Gate locked.")

    @property
    def state(self):
        return self.machine.state

    @property
    def mode(self):
        return self.machine.mode

    @property
    def hardware(self):
        return STATE_OUTPUTS[self.state]

    def record(self, message: str, transition: Transition | None = None):
        self.events.append({
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "mode": self.mode,
            "previous_state": transition.previous.value if transition else self.state.value,
            "input": transition.input.value if transition else "",
            "next_state": self.state.value,
            "output": transition.output if transition else "",
            "event": message,
        })

    def switch_mode(self, mode: str):
        if mode not in {"Moore", "Mealy"}:
            raise ValueError("Choose Moore or Mealy")
        if mode == self.mode:
            return
        machine_class = MooreMachine if mode == "Moore" else MealyMachine
        self.machine = machine_class(self.state)
        self.record(f"Switched to {mode}. Gate state preserved: {self.state.value}.")

    def process(self, gate_input: GateInput) -> Transition:
        transition = self.machine.process(gate_input)
        self.history.append(transition)
        self.entries += int(transition.entry_confirmed)
        self.alarm_events += int(transition.previous != GateState.ALARM
                                 and transition.current == GateState.ALARM)
        self.record(f"{transition.input.label}. {transition.previous.value} -> "
                    f"{transition.current.value}. {transition.output}.", transition)
        return transition

    def scan_card(self, force_invalid=False) -> Transition:
        """Validate the card before producing one of the FSM's existing inputs."""
        valid = not force_invalid and self.card.can_pay(self.fare)
        previous = self.state
        transition = self.process(GateInput.VALID_CARD if valid else GateInput.INVALID_CARD)
        if previous == GateState.ALARM:
            message = "Access blocked: alarm active. Reset the alarm before scanning. No fare charged."
        elif previous == GateState.UNLOCKED:
            message = "Gate already open. Complete entry before scanning again. No additional fare charged."
        elif valid:
            self.card.charge(self.fare)
            message = f"Access granted. Fare {currency(self.fare)} charged. Remaining balance: {currency(self.card.balance)}."
        elif force_invalid or not self.card.active:
            message = "Invalid or blocked card. No fare charged."
        else:
            message = f"Insufficient balance: {currency(self.card.balance)} available; fare {currency(self.fare)}. Recharge your card."
        self.card_message = message
        self.record(f"Card {self.card.card_id}: {message}")
        return transition

    def check_balance(self):
        message = f"Card balance: {currency(self.card.balance)}. Fare: {currency(self.fare)}."
        if not self.card.active:
            message += " Card is blocked."
        elif self.card.balance < self.fare:
            message += " Insufficient balance. Recharge before scanning."
        else:
            message += " Sufficient balance for entry."
        self.card_message = message
        self.record(message)
        return self.card.balance

    def recharge_card(self, amount):
        amount = money(amount)
        self.card.recharge(amount)
        self.card_message = f"Recharge successful: {currency(amount)} added. Balance: {currency(self.card.balance)}."
        self.record(self.card_message)

    def set_card_active(self, active: bool):
        self.card.active = bool(active)
        self.card_message = f"Card is now {'active' if self.card.active else 'blocked'}. Balance: {currency(self.card.balance)}."
        self.record(self.card_message)

    def export_csv(self, path: str | Path):
        with Path(path).open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "mode", "previous_state",
                                                     "input", "next_state", "output", "event"])
            writer.writeheader()
            writer.writerows(self.events)
