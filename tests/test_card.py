from decimal import Decimal
import unittest

from fsm.simulator import Simulator
from models.gate_input import GateInput as I
from models.gate_state import GateState as S
from models.metro_card import MetroCard


class CardTests(unittest.TestCase):
    def test_scan_deducts_one_fare_in_both_modes(self):
        for mode in ("Moore", "Mealy"):
            with self.subTest(mode=mode):
                session = Simulator(mode)
                result = session.scan_card()
                self.assertEqual(result.input, I.VALID_CARD)
                self.assertEqual(session.state, S.UNLOCKED)
                self.assertEqual(session.card.balance, Decimal("80.00"))
                session.scan_card()
                self.assertEqual(session.card.balance, Decimal("80.00"))
                session.process(I.PUSH_GATE)
                self.assertEqual(session.card.balance, Decimal("80.00"))
                self.assertEqual(session.entries, 1)

    def test_insufficient_balance_and_exact_fare(self):
        for mode in ("Moore", "Mealy"):
            with self.subTest(mode=mode):
                session = Simulator(mode, MetroCard(balance="19.99"))
                result = session.scan_card()
                self.assertEqual(result.input, I.INVALID_CARD)
                self.assertEqual(result.current, S.LOCKED)
                self.assertFalse(result.hardware.alarm)
                self.assertEqual(session.card.balance, Decimal("19.99"))
                self.assertIn("Insufficient balance", session.card_message)
                session.recharge_card("0.01")
                session.scan_card()
                self.assertEqual(session.state, S.UNLOCKED)
                self.assertEqual(session.card.balance, Decimal("0.00"))

    def test_alarm_and_mode_switch_never_charge_again(self):
        session = Simulator()
        session.process(I.PUSH_GATE)
        session.scan_card()
        session.switch_mode("Mealy")
        session.scan_card()
        self.assertEqual(session.state, S.ALARM)
        self.assertEqual(session.card.balance, Decimal("100.00"))
        session.process(I.AUTHORIZED_RESET)
        session.scan_card()
        self.assertEqual(session.card.balance, Decimal("80.00"))
        session.switch_mode("Moore")
        self.assertEqual(session.card.balance, Decimal("80.00"))

    def test_blocked_card_is_rejected_even_with_funds(self):
        session = Simulator(card=MetroCard(active=False))
        session.scan_card()
        self.assertEqual(session.state, S.LOCKED)
        self.assertEqual(session.card.balance, Decimal("100.00"))
        session.set_card_active(True)
        session.scan_card(force_invalid=True)
        self.assertEqual(session.state, S.LOCKED)
        self.assertEqual(session.card.balance, Decimal("100.00"))

    def test_check_and_recharge_do_not_change_fsm_or_charge(self):
        session = Simulator()
        session.process(I.TAILGATE_DETECTED)
        transitions = len(session.history)
        session.check_balance()
        session.recharge_card("50.25")
        self.assertEqual(session.card.balance, Decimal("150.25"))
        self.assertEqual(session.state, S.ALARM)
        self.assertEqual(len(session.history), transitions)
        self.assertIn("Recharge successful", session.events[-1]["event"])

    def test_invalid_recharges_leave_balance_unchanged(self):
        session = Simulator()
        for amount in ("0", "-1", "abc", "NaN", "Infinity", "1.001", "", None):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    session.recharge_card(amount)
                self.assertEqual(session.card.balance, Decimal("100.00"))


if __name__ == "__main__":
    unittest.main()
