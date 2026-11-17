from dataclasses import dataclass


@dataclass(frozen=True)
class GateOutput:
    """Persistent hardware status; the Moore output alphabet."""

    gate: str
    indicator: str
    alarm: bool

    @property
    def message(self) -> str:
        return f"Gate {self.gate.lower()} | {self.indicator} indicator | Alarm {'ON' if self.alarm else 'OFF'}"
