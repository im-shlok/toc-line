import customtkinter as ctk

from models.gate_input import GateInput as I
from models.gate_state import GateState as S
from ui import theme as t


class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, on_input):
        super().__init__(parent, fg_color=t.SURFACE, corner_radius=12)
        self.buttons = {}
        t.label(self, "Passenger actions", 18, True).pack(anchor="w", padx=22, pady=(18, 2))
        t.label(self, "Send an input to the selected machine.", 13, color=t.MUTED).pack(anchor="w", padx=22, pady=(0, 12))
        actions = [
            (I.VALID_CARD, "Valid card", "Scan your card and check the fare balance.", True),
            (I.INVALID_CARD, "Invalid card", "A simulated rejected card scan.", False),
            (I.PUSH_GATE, "Push gate", "Pass through, or attempt forced entry.", False),
            (I.TAILGATE_DETECTED, "Tailgate detected", "Trigger the simulated security sensor.", False),
            (I.AUTHORIZED_RESET, "Reset alarm", "Simulate a reset by authorized staff.", False),
        ]
        for gate_input, text, hint, primary in actions:
            opts = {}
            if gate_input == I.TAILGATE_DETECTED:
                opts.update(fg_color=t.RED_SOFT, hover_color="#F4D9DF", text_color=t.RED)
            widget = t.button(self, text, lambda value=gate_input: on_input(value), primary, **opts)
            widget.pack(fill="x", padx=22, pady=(0, 2))
            self.buttons[gate_input] = widget
            t.label(self, hint, 12, color=t.MUTED).pack(anchor="w", padx=24, pady=(0, 12))
        self.note = t.label(self, "Simulation only. No physical sensors connected.", 12, color=t.MUTED,
                            wraplength=270, justify="left")
        self.note.pack(anchor="w", padx=22, pady=(0, 18))

    def update_state(self, state):
        self.buttons[I.PUSH_GATE].configure(text="Push gate / enter" if state == S.UNLOCKED else "Push gate")
        self.buttons[I.AUTHORIZED_RESET].configure(
            fg_color=t.NAV if state == S.ALARM else t.SOFT,
            hover_color=t.PRIMARY if state == S.ALARM else t.BORDER,
            text_color=t.SURFACE if state == S.ALARM else t.INK)
