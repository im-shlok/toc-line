"""Simulated stored-value metro card; currency uses Decimal, never floats."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


def money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Enter a non-negative amount with at most two decimal places.")
        return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Enter a valid amount with at most two decimal places.") from exc


def currency(amount: Decimal) -> str:
    return f"₹{amount:,.2f}"


@dataclass
class MetroCard:
    card_id: str = "SM 2048 1357"
    balance: Decimal = Decimal("100.00")
    active: bool = True

    def __post_init__(self):
        self.balance = money(self.balance)

    def can_pay(self, fare: Decimal) -> bool:
        return self.active and self.balance >= money(fare)

    def recharge(self, amount) -> Decimal:
        amount = money(amount)
        if amount <= 0:
            raise ValueError("Enter a recharge amount greater than zero.")
        self.balance += amount
        return self.balance

    def charge(self, fare) -> None:
        fare = money(fare)
        if not self.can_pay(fare):
            raise ValueError("The card is blocked or has insufficient balance.")
        self.balance -= fare
