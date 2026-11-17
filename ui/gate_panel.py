import customtkinter as ctk
import tkinter as tk

from models.gate_state import GateState
from models.metro_card import currency
from ui import theme as t


class GatePanel(ctk.CTkFrame):
    """Turnstile with a draggable metro card, fare balance and physical outputs."""

    def __init__(self, parent, on_scan, on_check, on_recharge, on_card_status):
        super().__init__(parent, fg_color=t.SURFACE, corner_radius=12)
        self.state = GateState.LOCKED
        self.on_scan = on_scan
        self.card = None
        self.card_placed = False
        self.dragging = False
        self._last_pointer = (0, 0)
        self.reader_bounds = (0, 0, 0, 0)
        self.title = t.label(self, "Gate locked", 24, True)
        self.title.pack(anchor="w", padx=24, pady=(18, 0))
        self.description = t.label(self, "Scan a valid card to open the gate.", color=t.MUTED)
        self.description.pack(anchor="w", padx=24, pady=(2, 0))
        self.drawing = t.canvas(self, 320)
        self.drawing.pack(fill="x", padx=16, pady=(4, 0))
        self.drawing.bind("<Configure>", lambda _: self.draw())
        self.drawing.bind("<B1-Motion>", self._drag_card)
        self.drawing.bind("<ButtonRelease-1>", self._drop_card)
        self.drawing.bind("<Escape>", lambda _: self.return_card())
        card_info = ctk.CTkFrame(self, fg_color="transparent")
        card_info.pack(fill="x", padx=24, pady=(4, 8))
        self.balance_label = t.label(card_info, "", 13, True)
        self.balance_label.pack(side="left")
        self.card_status = ctk.CTkOptionMenu(card_info, values=["Card active", "Card blocked"],
            command=on_card_status, width=114, font=t.font(12), fg_color=t.SOFT,
            button_color=t.BORDER, button_hover_color=t.SOFT, text_color=t.INK,
            dropdown_fg_color=t.SURFACE, dropdown_text_color=t.INK, dropdown_hover_color=t.SOFT)
        self.card_status.pack(side="right")
        card_actions = ctk.CTkFrame(self, fg_color="transparent")
        card_actions.pack(fill="x", padx=24, pady=(0, 10))
        self.scan_button = t.button(card_actions, "Scan card", self.place_card, width=100, height=34, anchor="center")
        self.scan_button.pack(side="left", padx=(0, 6))
        self.check_button = t.button(card_actions, "Check balance", on_check, width=110, height=34, anchor="center")
        self.check_button.pack(side="left", padx=(0, 6))
        t.button(card_actions, "Return card", self.return_card, width=100, height=34, anchor="center").pack(side="left")
        recharge = ctk.CTkFrame(self, fg_color="transparent")
        recharge.pack(fill="x", padx=24, pady=(0, 10))
        t.label(recharge, "Recharge (₹)", 13).pack(side="left", padx=(0, 8))
        self.recharge_entry = ctk.CTkEntry(recharge, width=84, height=34, font=t.font(13),
                                         fg_color=t.SURFACE, border_color=t.BORDER, text_color=t.INK)
        self.recharge_entry.insert(0, "50")
        self.recharge_entry.pack(side="left", padx=(0, 8))
        self.recharge_entry.bind("<Return>", lambda _: on_recharge(self.recharge_entry.get()))
        self.recharge_button = t.button(recharge, "Add balance", lambda: on_recharge(self.recharge_entry.get()),
                                       width=112, height=34, anchor="center")
        self.recharge_button.pack(side="left")
        self.card_feedback = t.label(self, "", 13, color=t.MUTED, wraplength=350, justify="left")
        self.card_feedback.pack(fill="x", padx=24, pady=(0, 14))
        self.bind("<Configure>", lambda event: self.card_feedback.configure(
            wraplength=max(260, event.width / self._get_widget_scaling() - 48)))
        self.status = ctk.CTkFrame(self, fg_color=t.SOFT, corner_radius=8)
        self.status.pack(fill="x", padx=24, pady=(0, 18))
        self.values = {}
        for index, name in enumerate(("Gate", "Indicator", "Alarm")):
            self.status.grid_columnconfigure(index, weight=1, uniform="status")
            cell = ctk.CTkFrame(self.status, fg_color="transparent")
            cell.grid(row=0, column=index, sticky="ew", padx=12, pady=10)
            t.label(cell, name, 12, color=t.MUTED).pack(anchor="w")
            value = t.label(cell, "", 15, True)
            value.pack(anchor="w")
            self.values[name] = value

    def update_state(self, state, hardware):
        self.state = state
        color = {GateState.LOCKED: t.AMBER, GateState.UNLOCKED: t.GREEN, GateState.ALARM: t.RED}[state]
        self.title.configure(text={GateState.LOCKED: "Gate locked", GateState.UNLOCKED: "Gate open",
                                   GateState.ALARM: "Security alarm active"}[state], text_color=color)
        self.description.configure(text={
            GateState.LOCKED: "Scan a valid card to open the gate.",
            GateState.UNLOCKED: "Access granted. Push the gate to complete entry.",
            GateState.ALARM: "Access suspended. An authorized reset is required.",
        }[state])
        self.values["Gate"].configure(text=hardware.gate)
        self.values["Indicator"].configure(text=hardware.indicator,
                                          text_color=t.GREEN if hardware.indicator == "Green" else t.RED)
        self.values["Alarm"].configure(text="ON" if hardware.alarm else "OFF",
                                      text_color=t.RED if hardware.alarm else t.MUTED)
        self.draw()

    def update_card(self, session):
        self.card = session.card
        self.balance_label.configure(text=f"Balance {currency(self.card.balance)}   Fare {currency(session.fare)}")
        self.card_status.set("Card active" if self.card.active else "Card blocked")
        self.card_feedback.configure(text=session.card_message,
            text_color=t.RED if session.card_message.startswith(("Insufficient", "Invalid", "Access blocked", "Recharge failed")) else t.MUTED)
        self.recharge_entry.configure(border_color=t.RED if session.card_message.startswith("Recharge failed") else t.BORDER)
        self.draw()

    def draw(self):
        if self.dragging:
            return
        c = self.drawing
        c.delete("all")
        width = max(c.winfo_width(), 340)
        scale = min(1.25, width / 500)
        height = int(320 * scale)
        if int(c.cget("height")) != height:
            c.configure(height=height)
        middle = width * .62
        color = t.GREEN if self.state == GateState.UNLOCKED else t.RED
        def rect(x1, y1, x2, y2, **kwargs):
            return c.create_rectangle(middle+x1*scale, y1*scale, middle+x2*scale, y2*scale, **kwargs)
        def line(x1, y1, x2, y2, **kwargs):
            return c.create_line(middle+x1*scale, y1*scale, middle+x2*scale, y2*scale, **kwargs)
        # Top-down turnstile plan. The two flaps retract into the housings.
        rect(-150, 25, 150, 157, fill=t.BG, outline="")
        line(0, 31, 0, 148, fill=t.BORDER, width=2, dash=(4, 6))
        for left in (-143, 78):
            rect(left, 39, left+65, 141, fill=t.BORDER, outline="")
            rect(left+8, 47, left+57, 133, fill=t.NAV, outline="")
            rect(left+17, 58, left+48, 83, fill=t.SURFACE, outline="")
            c.create_oval(middle+(left+27)*scale, 64*scale, middle+(left+38)*scale, 75*scale, fill=color, outline="")
            line(left+22, 107, left+43, 107, fill=t.NAV_TEXT, width=2)
            line(left+22, 114, left+43, 114, fill=t.NAV_TEXT, width=2)
        self.reader_bounds = (middle-149*scale, 40*scale, middle-72*scale, 96*scale)
        c.create_rectangle(*self.reader_bounds, outline=t.PRIMARY, width=2, dash=(5, 3), tags="reader")
        c.create_text(middle-110*scale, 17*scale, text="Card reader", font=(t.FONT, -int(13*scale), "bold"), fill=t.PRIMARY)
        if self.state == GateState.UNLOCKED:
            rect(-78, 98, -66, 129, fill=t.GREEN, outline="")
            rect(66, 98, 78, 129, fill=t.GREEN, outline="")
            line(0, 125, 0, 65, fill=t.GREEN, width=5, arrow="last", arrowshape=(12, 14, 8))
        else:
            rect(-78, 97, -3, 121, fill=color, outline="")
            rect(3, 97, 78, 121, fill=color, outline="")
            line(-8, 56, 8, 72, fill=color, width=3)
            line(8, 56, -8, 72, fill=color, width=3)
        caption = "Passage clear" if self.state == GateState.UNLOCKED else "Passage closed"
        c.create_text(middle, 174*scale, text=caption, font=(t.FONT, -int(13*scale)), fill=t.MUTED)
        card_width, card_height = 192*scale, 112*scale
        if self.card_placed:
            left = (self.reader_bounds[0]+self.reader_bounds[2]-card_width)/2
            top = (self.reader_bounds[1]+self.reader_bounds[3]-card_height)/2
        else:
            left, top = 22*scale, 190*scale
        self.card_bounds = (left, top, left+card_width, top+card_height)
        self._draw_card(left, top, card_width, card_height, scale)
        c.create_text(width*.65, 246*scale,
            text="Card placed on reader.\nDrag it away, or return it below." if self.card_placed else "Drag the card onto\nthe reader on the machine.",
            font=(t.FONT, -int(13*scale)), fill=t.MUTED, justify="left", width=int(width*.42))
        c.tag_bind("card", "<ButtonPress-1>", self._start_drag)
        c.tag_bind("card", "<Enter>", lambda _: c.configure(cursor="hand2"))
        c.tag_bind("card", "<Leave>", lambda _: c.configure(cursor="" if not self.dragging else "fleur"))

    def _draw_card(self, x, y, width, height, scale):
        c = self.drawing
        radius = 12*scale
        points = [x+radius, y, x+width-radius, y, x+width, y, x+width, y+radius,
                  x+width, y+height-radius, x+width, y+height, x+width-radius, y+height,
                  x+radius, y+height, x, y+height, x, y+height-radius, x, y+radius, x, y]
        c.create_polygon(points, smooth=True, fill=t.NAV, outline="", tags="card")
        c.create_text(x+15*scale, y+22*scale, text="SmartMetro", anchor="w",
                      font=(t.FONT, -int(17*scale), "bold"), fill=t.SURFACE, tags="card")
        # Contactless symbol is drawn with consistent strokes, not a font glyph.
        for extent in (8, 15, 22):
            c.create_arc(x+width-38*scale-extent*scale/2, y+12*scale-extent*scale/2,
                         x+width-38*scale+extent*scale/2, y+12*scale+extent*scale/2,
                         start=-45, extent=90, style=tk.ARC, outline=t.NAV_TEXT, width=2, tags="card")
        c.create_text(x+15*scale, y+51*scale, text="Stored balance", anchor="w",
                      font=(t.FONT, -int(11*scale)), fill=t.NAV_TEXT, tags="card")
        c.create_text(x+15*scale, y+72*scale, text=currency(self.card.balance) if self.card else "₹100.00", anchor="w",
                      font=(t.FONT, -int(22*scale), "bold"), fill=t.SURFACE, tags="card")
        c.create_text(x+15*scale, y+97*scale, text=self.card.card_id if self.card else "SM 2048 1357", anchor="w",
                      font=(t.FONT, -int(11*scale)), fill=t.NAV_TEXT, tags="card")

    def _start_drag(self, event):
        self.dragging = True
        self._last_pointer = (event.x, event.y)
        self.drawing.grab_set()
        self.drawing.focus_set()
        self.drawing.configure(cursor="fleur")
        self.drawing.tag_raise("card")

    def _over_reader(self):
        bounds = self.drawing.bbox("card")
        if bounds is None:
            return False
        x, y = (bounds[0]+bounds[2])/2, (bounds[1]+bounds[3])/2
        left, top, right, bottom = self.reader_bounds
        return left <= x <= right and top <= y <= bottom

    def _drag_card(self, event):
        if not self.dragging:
            return
        dx, dy = event.x-self._last_pointer[0], event.y-self._last_pointer[1]
        self.drawing.move("card", dx, dy)
        self._last_pointer = (event.x, event.y)
        self.drawing.itemconfigure("reader", outline=t.GREEN if self._over_reader() else t.PRIMARY,
                                    width=4 if self._over_reader() else 2)

    def _drop_card(self, event):
        if not self.dragging:
            return
        self._drag_card(event)
        placed = self._over_reader()
        self.dragging = False
        self.drawing.grab_release()
        self.drawing.configure(cursor="")
        self.card_placed = placed
        self.draw()
        if placed:
            self.on_scan()

    def place_card(self):
        self.card_placed = True
        self.draw()
        self.on_scan()

    def return_card(self):
        if self.dragging:
            self.drawing.grab_release()
        self.dragging = False
        self.card_placed = False
        self.drawing.configure(cursor="")
        self.draw()


class StateDiagram(ctk.CTkFrame):
    """A compact shared transition overview; full self-loops live in the table."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=t.SURFACE, corner_radius=12)
        self.state = GateState.LOCKED
        t.label(self, "State map", 16, True).pack(anchor="w", padx=22, pady=(14, 0))
        self.drawing = t.canvas(self, 170)
        self.drawing.pack(fill="x", padx=14)
        self.drawing.bind("<Configure>", lambda _: self.draw())

    def update_state(self, state):
        self.state = state
        self.draw()

    def draw(self):
        c = self.drawing
        c.delete("all")
        width = max(c.winfo_width(), 340)
        left, right, middle = width*.23, width*.77, width*.5
        colors = {GateState.LOCKED: t.AMBER, GateState.UNLOCKED: t.GREEN, GateState.ALARM: t.RED}
        c.create_line(left+49, 38, right-49, 38, fill=t.MUTED, arrow="last", width=2)
        c.create_text(middle, 24, text="Valid card", font=(t.FONT, 9), fill=t.MUTED)
        c.create_line(right-49, 66, left+49, 66, fill=t.MUTED, arrow="last", width=2)
        c.create_text(middle, 79, text="Push gate", font=(t.FONT, 9), fill=t.MUTED)
        c.create_line(left, 75, middle-50, 114, fill=t.BORDER, arrow="last", width=2)
        c.create_line(right, 75, middle+50, 114, fill=t.BORDER, arrow="last", width=2)
        c.create_text(left-8, 111, text="Push / tailgate", font=(t.FONT, 9), fill=t.MUTED)
        c.create_text(right+3, 111, text="Tailgate", font=(t.FONT, 9), fill=t.MUTED)
        for state, x, y in ((GateState.LOCKED, left, 51), (GateState.UNLOCKED, right, 51),
                            (GateState.ALARM, middle, 125)):
            active = state == self.state
            c.create_rectangle(x-48, y-19, x+48, y+19,
                               fill=colors[state] if active else t.SOFT, outline="")
            c.create_text(x, y, text=state.value, font=(t.FONT, 10, "bold"),
                          fill=t.SURFACE if active else t.INK)
        # Recovery is explicit; same-state transitions are disclosed in the full table.
        c.create_text(middle, 155, text="ALARM + authorized reset returns to LOCKED. Self-loops: see table.",
                      font=(t.FONT, 9), fill=t.MUTED)
