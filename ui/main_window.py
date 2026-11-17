import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from fsm.mealy_machine import MealyMachine
from fsm.moore_machine import MooreMachine
from fsm.simulator import Simulator
from fsm.transition_manager import TRANSITIONS
from models.gate_input import GateInput as I
from models.gate_state import GateState as S
from ui import theme as t
from ui.activity_panel import ActivityPanel
from ui.alarm_sound import AlarmSound
from ui.control_panel import ControlPanel
from ui.gate_panel import GatePanel, StateDiagram


class SmartMetroApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        super().__init__()
        self.title("SmartMetro | Intelligent Metro Turnstile Controller")
        scaling = self._get_window_scaling()
        width = min(1260, int(self.winfo_screenwidth() / scaling) - 80)
        height = min(900, int(self.winfo_screenheight() / scaling) - 90)
        self.geometry(f"{max(980, width)}x{max(680, height)}")
        self.minsize(980, 680)
        self.configure(fg_color=t.BG)
        self.session = Simulator()
        self.alarm_sound = AlarmSound(self)
        self.last_transition = None
        self.scenario_id = None
        self.scenario_running = False
        self.view = "Simulator"
        self.mode_var = tk.StringVar(value="Moore")
        self.active_view_var = tk.StringVar(value="Simulator")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_menu()
        self._build_simulator()
        self._build_table()
        self._build_comparison()
        self._build_guide()
        self.show_view("Simulator")
        self.refresh()
        self.bind("<Control-e>", lambda _: self.export_log())
        self.bind("<Control-Key-1>", lambda _: self.show_view("Simulator"))
        self.bind("<Control-Key-2>", lambda _: self.show_view("Transition table"))
        self.bind("<Control-Key-3>", lambda _: self.show_view("Compare machines"))
        self.bind("<Escape>", lambda _: self.stop_scenario())
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=190, corner_radius=0, fg_color=t.NAV)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(28, 5))
        mark = t.canvas(brand, 37, t.NAV)
        mark.configure(width=37)
        mark.pack(side="left", padx=(0, 9))
        mark.create_rectangle(3, 3, 34, 29, outline=t.NAV_TEXT, width=2)
        mark.create_rectangle(9, 9, 28, 18, outline=t.NAV_TEXT, width=2)
        mark.create_oval(9, 22, 13, 26, fill=t.NAV_TEXT, outline="")
        mark.create_oval(24, 22, 28, 26, fill=t.NAV_TEXT, outline="")
        mark.create_line(11, 29, 7, 35, fill=t.NAV_TEXT, width=2)
        mark.create_line(26, 29, 30, 35, fill=t.NAV_TEXT, width=2)
        t.label(brand, "SmartMetro", 18, True, t.SURFACE).pack(side="left")
        t.label(self.sidebar, "Turnstile controller", 12, color=t.NAV_TEXT).pack(anchor="w", padx=20, pady=(0, 32))
        self.nav_buttons = {}
        for name in ("Simulator", "Transition table", "Compare machines", "Quick guide"):
            widget = t.button(self.sidebar, name, lambda value=name: self.show_view(value),
                              width=154, fg_color="transparent", hover_color="#294953",
                              text_color=t.NAV_TEXT, height=43, font=t.font(13))
            widget.pack(fill="x", padx=14, pady=4)
            self.nav_buttons[name] = widget
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=20, pady=24)
        t.label(bottom, "Theory in motion", 14, True, t.SURFACE).pack(anchor="w")
        t.label(bottom, "Mealy & Moore FSMs\nLocal desktop simulation", 12, color=t.NAV_TEXT,
                justify="left").pack(anchor="w", pady=(6, 0))

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        top = ctk.CTkFrame(main, fg_color=t.SURFACE, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        self.page_title = t.label(top, "Turnstile simulator", 25, True)
        self.page_title.pack(side="left", padx=28, pady=20)
        self.mode_select = ctk.CTkSegmentedButton(top, values=["Moore", "Mealy"],
                    variable=self.mode_var, command=self.switch_mode, font=t.font(13, "bold"), height=36,
                    fg_color=t.SOFT, selected_color=t.PRIMARY, selected_hover_color=t.PRIMARY_HOVER,
                    unselected_color=t.SOFT, unselected_hover_color=t.BORDER, text_color=t.INK)
        self.mode_select.pack(side="right", padx=28)
        # Provide an always-accessible native menu alternative to this segmented control.
        self.toolbar = ctk.CTkFrame(main, fg_color="transparent")
        self.toolbar.grid(row=1, column=0, sticky="ew", padx=28, pady=(16, 10))
        self.summary = t.label(self.toolbar, "", 13, color=t.MUTED)
        self.summary.pack(side="left")
        self.scenario_var = tk.StringVar(value="Successful entry")
        self.scenario_select = ctk.CTkOptionMenu(self.toolbar, values=["Successful entry", "Unauthorized push", "Tailgating"],
                    variable=self.scenario_var, fg_color=t.SURFACE, button_color=t.BORDER,
                    button_hover_color=t.SOFT, text_color=t.INK, dropdown_fg_color=t.SURFACE,
                    dropdown_text_color=t.INK, dropdown_hover_color=t.SOFT, font=t.font(12), width=156)
        self.scenario_select.pack(side="right", padx=(0, 8))
        self.run_button = t.button(self.toolbar, "Run scenario", self.run_scenario, height=32, width=115, anchor="center")
        self.run_button.pack(side="right", padx=(8, 8))
        self.scroll = ctk.CTkScrollableFrame(main, fg_color="transparent", corner_radius=0)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        self.scroll.grid_columnconfigure(0, weight=1)
        self.pages = {}

    def _build_menu(self):
        menu = tk.Menu(self, tearoff=False)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Export activity log...", command=self.export_log, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        for index, name in enumerate(("Simulator", "Transition table", "Compare machines", "Quick guide"), 1):
            view_menu.add_radiobutton(label=name, variable=self.active_view_var, value=name,
                                     command=lambda value=name: self.show_view(value),
                                     accelerator=f"Ctrl+{index}" if index < 4 else "")
        menu.add_cascade(label="View", menu=view_menu)
        mode_menu = tk.Menu(menu, tearoff=False)
        for mode in ("Moore", "Mealy"):
            mode_menu.add_radiobutton(label=f"{mode} machine", variable=self.mode_var, value=mode,
                                     command=lambda value=mode: self.switch_mode(value))
        menu.add_cascade(label="FSM mode", menu=mode_menu)
        actions_menu = tk.Menu(menu, tearoff=False)
        for gate_input in I:
            actions_menu.add_command(label=gate_input.label, command=lambda value=gate_input: self.send_input(value))
        actions_menu.add_separator()
        actions_menu.add_command(label="Scan metro card (check fare)", command=self.scan_card)
        actions_menu.add_command(label="Check card balance", command=self.check_balance)
        actions_menu.add_command(label="Recharge card...", command=self.focus_recharge)
        menu.add_cascade(label="Actions", menu=actions_menu)
        self.scenario_menu = tk.Menu(menu, tearoff=False)
        for scenario in ("Successful entry", "Unauthorized push", "Tailgating"):
            self.scenario_menu.add_command(label=scenario, command=lambda value=scenario: self.run_scenario(value))
        self.scenario_menu.add_separator()
        self.scenario_menu.add_command(label="Stop scenario", command=self.stop_scenario, accelerator="Esc")
        menu.add_cascade(label="Scenarios", menu=self.scenario_menu)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Quick guide", command=lambda: self.show_view("Quick guide"))
        help_menu.add_command(label="About SmartMetro", command=self.about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.configure(menu=menu)
        self.menu_bar = menu

    def _new_page(self, name):
        page = ctk.CTkFrame(self.scroll, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages[name] = page
        return page

    def _build_simulator(self):
        page = self._new_page("Simulator")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0, minsize=315)
        self.gate_panel = GatePanel(page, self.scan_card, self.check_balance, self.recharge_card, self.set_card_status)
        self.gate_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16), pady=(0, 14))
        self.controls = ControlPanel(page, self.send_input)
        self.controls.grid(row=0, column=1, rowspan=2, sticky="new", pady=(0, 14))
        output_frame = ctk.CTkFrame(page, fg_color=t.SURFACE, corner_radius=12)
        output_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16), pady=(0, 14))
        self.output_heading = t.label(output_frame, "Moore output", 14, True)
        self.output_heading.pack(anchor="w", padx=22, pady=(14, 2))
        self.output_label = t.label(output_frame, "", 16, bold=True, wraplength=460, justify="left")
        self.output_label.pack(anchor="w", fill="x", padx=22, pady=(0, 4))
        self.output_note = t.label(output_frame, "", 12, color=t.MUTED, wraplength=460, justify="left")
        self.output_note.pack(anchor="w", fill="x", padx=22, pady=(0, 14))
        output_frame.bind("<Configure>", lambda event: self._wrap_outputs(event.width))
        self.diagram = StateDiagram(page)
        self.diagram.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.activity = ActivityPanel(page, self.export_log)
        self.activity.grid(row=3, column=0, columnspan=2, sticky="nsew")

    def _wrap_outputs(self, width):
        width = width / self.output_label._get_widget_scaling()
        self.output_label.configure(wraplength=max(250, width-44))
        self.output_note.configure(wraplength=max(250, width-44))

    def _build_table(self):
        page = self._new_page("Transition table")
        t.label(page, "Every state, every input", 22, True).pack(anchor="w", pady=(4, 8))
        t.label(page, "Both machines use this same transition function. The last action is highlighted.",
                color=t.MUTED).pack(anchor="w", pady=(0, 18))
        frame = ctk.CTkFrame(page, fg_color=t.SURFACE, corner_radius=12)
        frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(frame, columns=("state", "input", "next", "mealy", "moore"),
                                  show="headings", height=15, style="Metro.Treeview")
        for name, title, width in (("state", "Current state", 100), ("input", "Input", 165),
                                  ("next", "Next state", 100), ("mealy", "Mealy response", 240),
                                  ("moore", "Moore output (next state)", 310)):
            self.table.heading(name, text=title, anchor="w")
            self.table.column(name, width=width, minwidth=width, stretch=False)
        for state in S:
            for gate_input in I:
                current = TRANSITIONS[state][gate_input]
                self.table.insert("", "end", iid=f"{state.value}:{gate_input.value}",
                                  values=(state.value, gate_input.value, current.value,
                                          MealyMachine.output(state, gate_input), MooreMachine.output(current).message))
        bar = ttk.Scrollbar(frame, orient="horizontal", command=self.table.xview)
        self.table.configure(xscrollcommand=bar.set)
        self.table.pack(fill="both", expand=True, padx=14, pady=(14, 0))
        bar.pack(fill="x", padx=14, pady=(0, 14))
        t.label(page, "Select a row to inspect it. Use the Actions menu to send a real input to the simulator.",
                13, color=t.MUTED).pack(anchor="w", pady=14)

    def _build_comparison(self):
        page = self._new_page("Compare machines")
        t.label(page, "One transition. Two kinds of output.", 22, True).pack(anchor="w", pady=(4, 8))
        t.label(page, "Send an input from the Actions menu or simulator to compare both models.",
                color=t.MUTED).pack(anchor="w", pady=(0, 18))
        self.comparison_transition = t.label(page, "", 15, True)
        self.comparison_transition.pack(anchor="w", pady=(0, 14))
        columns = ctk.CTkFrame(page, fg_color="transparent")
        columns.pack(fill="x")
        self.compare_outputs = {}
        for index, (mode, equation, description) in enumerate((
                ("Mealy", "λ(q, x)", "Uses the state before the transition and the received input."),
                ("Moore", "λ(q′)", "Uses only the resulting state. Also defined before any input."))):
            columns.grid_columnconfigure(index, weight=1, uniform="compare")
            cell = ctk.CTkFrame(columns, fg_color=t.SURFACE, corner_radius=12)
            cell.grid(row=0, column=index, sticky="nsew", padx=(0, 12) if index == 0 else (0, 0))
            t.label(cell, mode, 22, True).pack(anchor="w", padx=22, pady=(22, 8))
            t.label(cell, equation, 24, color=t.PRIMARY).pack(anchor="w", padx=22, pady=(0, 12))
            t.label(cell, description, 14, color=t.MUTED, wraplength=330,
                    justify="left").pack(anchor="w", fill="x", padx=22, pady=(0, 18))
            output = t.label(cell, "", 18, True, wraplength=330, justify="left")
            output.pack(anchor="w", fill="x", padx=22, pady=(0, 22))
            self.compare_outputs[mode] = output
        note = ctk.CTkFrame(page, fg_color=t.SOFT, corner_radius=12)
        note.pack(fill="x", pady=20)
        t.label(note, "Why an invalid scan looks different", 17, True).pack(anchor="w", padx=22, pady=(18, 8))
        t.label(note, "In LOCKED, an invalid scan makes Mealy say ‘Access Denied’. Moore stays LOCKED, so its output "
                "remains gate closed, red indicator, alarm off. The activity log records the scan as an event; "
                "that event is not a Moore output. Input-specific Moore messages would require extra states.",
                14, color=t.MUTED, wraplength=770, justify="left").pack(anchor="w", fill="x", padx=22, pady=(0, 20))
        t.button(page, "Try an input in the simulator", lambda: self.show_view("Simulator"),
                 primary=True, width=240, anchor="center").pack(anchor="w")

    def _build_guide(self):
        page = self._new_page("Quick guide")
        t.label(page, "Your first journey", 22, True).pack(anchor="w", pady=(4, 10))
        guide = ctk.CTkTextbox(page, fg_color=t.SURFACE, corner_radius=12, font=t.font(15),
                              text_color=t.INK, height=530, wrap="word")
        guide.pack(fill="both", expand=True)
        guide.insert("1.0", "Start with a locked gate\n\n"
            "1. Choose Moore or Mealy using the mode selector or FSM mode menu.\n"
            "2. Click Valid card. The gate becomes UNLOCKED.\n"
            "3. Click Push gate / enter. A passenger passes and the gate returns to LOCKED.\n"
            "4. Inspect the activity log and Compare machines to see how the output was generated.\n\n"
            "Try a security event\n\n"
            "Push a locked gate or click Tailgate detected to enter ALARM. Card scans cannot clear it. "
            "A repeating sound plays while ALARM is active. Use Reset alarm to simulate an authorized staff reset "
            "and stop the sound. Changing FSM modes preserves the gate state and alarm sound.\n\n"
            "Use the metro card\n\n"
            "Drag the SmartMetro card onto the highlighted card reader on the turnstile itself. "
            "Release it there to scan. The card stays on the reader; drag it away or use Return card. "
            "Scan card provides the same action by button or keyboard. The demo card starts with ₹100 and the fare is ₹20. "
            "Check balance shows available funds. Add balance recharges the card. Card blocked simulates an inactive card. "
            "A successful scan of a locked gate deducts one fare. Scans while open or in ALARM do not charge again. "
            "An insufficient balance produces INVALID_CARD and is logged as a card event, separate from Moore output.\n\n"
            "Interactive menu\n\n"
            "File exports the activity log as CSV. View changes pages. FSM mode changes the selected model. "
            "Actions sends any of the five inputs from any page. Scenarios runs a short demonstration and can be stopped. "
            "Help opens this guide and the application information.\n\n"
            "Keyboard controls\n\n"
            "Tab moves between controls; Enter or Space activates a focused action button. "
            "Ctrl+1 opens Simulator, Ctrl+2 the Transition table, Ctrl+3 Compare machines. "
            "Ctrl+E exports the log. Escape stops a running scenario. Alt opens the native menu.\n\n"
            "Reading the outputs\n\n"
            "Moore output is persistent gate, indicator and alarm status. Mealy output is the response to the latest input. "
            "Physical gate status is shown in both modes. Each logged transition includes its mode, input and output.\n\n"
            "Simulation boundaries\n\n"
            "Cards, tailgating sensors and staff authorization are simulated. No physical gate, payment system, camera "
            "or login is connected. Entry counts increase only when an unlocked gate is pushed.")
        guide.configure(state="disabled")

    def show_view(self, name):
        if name not in self.pages:
            return
        for page in self.pages.values():
            page.grid_forget()
        self.pages[name].grid(row=0, column=0, sticky="nsew", padx=6, pady=4)
        self.view = name
        self.active_view_var.set(name)
        self.page_title.configure(text="Turnstile simulator" if name == "Simulator" else name)
        for value, widget in self.nav_buttons.items():
            widget.configure(fg_color="#2C515B" if value == name else "transparent",
                             text_color=t.SURFACE if value == name else t.NAV_TEXT)
        self.scroll._parent_canvas.yview_moveto(0)

    def switch_mode(self, mode):
        self.stop_scenario()
        self.session.switch_mode(mode)
        self.mode_var.set(mode)
        self.refresh()

    def send_input(self, gate_input, from_scenario=False):
        if not from_scenario:
            self.stop_scenario()
        if gate_input in (I.VALID_CARD, I.INVALID_CARD):
            self.last_transition = self.session.scan_card(force_invalid=gate_input == I.INVALID_CARD)
        else:
            self.last_transition = self.session.process(gate_input)
        self.refresh()

    def scan_card(self):
        self.stop_scenario()
        self.gate_panel.card_placed = True
        self.last_transition = self.session.scan_card()
        self.refresh()

    def check_balance(self):
        self.session.check_balance()
        self.refresh()

    def recharge_card(self, amount):
        try:
            self.session.recharge_card(amount)
        except ValueError as exc:
            self.session.card_message = f"Recharge failed: {exc}"
            self.session.record(self.session.card_message)
        self.refresh()

    def set_card_status(self, status):
        self.session.set_card_active(status == "Card active")
        self.refresh()

    def focus_recharge(self):
        self.show_view("Simulator")
        self.scroll._parent_canvas.yview_moveto(0)
        self.gate_panel.recharge_entry.focus_set()

    def refresh(self):
        session = self.session
        self.alarm_sound.set_active(session.hardware.alarm)
        for mode, widget in self.mode_select._buttons_dict.items():
            widget.configure(text_color=t.SURFACE if mode == session.mode else t.INK)
        self.summary.configure(text=f"{session.state.value}   |   Entries: {session.entries}   |   Alarm events: {session.alarm_events}")
        self.gate_panel.update_state(session.state, session.hardware)
        self.gate_panel.update_card(session)
        self.controls.update_state(session.state)
        self.diagram.update_state(session.state)
        self.output_heading.configure(text=f"{session.mode} output")
        if session.mode == "Moore":
            output = session.hardware.message
            note = "Persistent output determined only by the current state."
        elif self.last_transition and self.last_transition.mode == "Mealy":
            output = self.last_transition.output
            note = f"Latest response to {self.last_transition.input.value}, from {self.last_transition.previous.value}."
        else:
            output = "Waiting for an input"
            note = "Mealy produces a response when an input is received."
        self.output_label.configure(text=output)
        self.output_note.configure(text=note)
        self.activity.sync(session)
        if self.last_transition:
            result = self.last_transition
            self.comparison_transition.configure(text=f"Latest action: {result.previous.value} + {result.input.value} → {result.current.value}")
            self.compare_outputs["Mealy"].configure(text=MealyMachine.output(result.previous, result.input))
            self.compare_outputs["Moore"].configure(text=MooreMachine.output(result.current).message)
            row = f"{result.previous.value}:{result.input.value}"
            self.table.selection_set(row)
            self.table.see(row)
        else:
            self.comparison_transition.configure(text="Initial state: LOCKED. No input received yet.")
            self.compare_outputs["Mealy"].configure(text="Waiting for an input")
            self.compare_outputs["Moore"].configure(text=session.hardware.message)

    def run_scenario(self, name=None):
        if self.scenario_running and name is None:
            self.stop_scenario()
            return
        self.stop_scenario()
        name = name or self.scenario_var.get()
        self.scenario_var.set(name)
        sequences = {
            "Successful entry": [I.VALID_CARD, I.PUSH_GATE],
            "Unauthorized push": [I.PUSH_GATE, I.VALID_CARD, I.AUTHORIZED_RESET],
            "Tailgating": [I.VALID_CARD, I.TAILGATE_DETECTED, I.AUTHORIZED_RESET],
        }
        steps = sequences[name].copy()
        # Establish LOCKED using only the five allowed inputs; no hidden reset.
        if self.session.state == S.ALARM:
            steps.insert(0, I.AUTHORIZED_RESET)
        elif self.session.state == S.UNLOCKED:
            steps.insert(0, I.PUSH_GATE)
        self.session.record(f"Scenario started: {name}.")
        self.scenario_running = True
        self.run_button.configure(text="Stop scenario")
        self.show_view("Simulator")
        self.refresh()

        def advance():
            self.scenario_id = None
            if not self.scenario_running:
                return
            if not steps:
                self.scenario_running = False
                self.run_button.configure(text="Run scenario")
                self.session.record(f"Scenario complete: {name}.")
                self.refresh()
                return
            self.send_input(steps.pop(0), from_scenario=True)
            self.scenario_id = self.after(1000, advance)

        self.scenario_id = self.after(250, advance)

    def stop_scenario(self):
        if self.scenario_id is not None:
            self.after_cancel(self.scenario_id)
            self.scenario_id = None
        if self.scenario_running:
            self.scenario_running = False
            self.run_button.configure(text="Run scenario")
            self.session.record("Scenario stopped. Current gate state preserved.")
            self.activity.sync(self.session)

    def export_log(self):
        path = filedialog.asksaveasfilename(parent=self, title="Export activity log", defaultextension=".csv",
                initialfile="smartmetro-activity.csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            self.session.export_csv(path)
        except OSError as exc:
            messagebox.showerror("Export failed", f"Could not save the activity log.\n{exc}", parent=self)
        else:
            messagebox.showinfo("Activity log exported", f"Saved {len(self.session.events)} events to:\n{path}", parent=self)

    def about(self):
        messagebox.showinfo("About SmartMetro", "SmartMetro\nIntelligent Metro Turnstile Controller\n\n"
            "An interactive demonstration of Mealy and Moore finite state machines.\n"
            "Python + CustomTkinter. All access and security inputs are simulated.", parent=self)

    def close(self):
        self.stop_scenario()
        self.alarm_sound.stop()
        self.destroy()
