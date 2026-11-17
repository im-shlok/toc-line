"""Exercise the real desktop widgets and event loop; no screenshots are created."""
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.gate_input import GateInput as I
from models.gate_state import GateState as S
from ui.main_window import SmartMetroApp


def run():
    app = SmartMetroApp()
    errors = []
    app.report_callback_exception = lambda *args: errors.append(args)
    try:
        app.update()
        assert app.session.state == S.LOCKED
        assert not app.alarm_sound.active
        assert len(app.table.get_children()) == 15
        assert app.gate_panel.values["Gate"].cget("text") == "Closed"
        assert app.compare_outputs["Mealy"].cget("text") == "Waiting for an input"
        assert app.menu_bar.index("end") == 5

        # Button callbacks update both the real hardware status and model response.
        app.controls.buttons[I.VALID_CARD].invoke()
        app.update()
        assert app.session.state == S.UNLOCKED
        assert app.gate_panel.values["Gate"].cget("text") == "Open"
        app.controls.buttons[I.PUSH_GATE].invoke()
        assert app.session.state == S.LOCKED and app.session.entries == 1
        app.switch_mode("Mealy")
        app.controls.buttons[I.INVALID_CARD].invoke()
        assert app.output_label.cget("text") == "Access Denied"
        assert "Gate closed" in app.compare_outputs["Moore"].cget("text")
        app.controls.buttons[I.PUSH_GATE].invoke()
        assert app.output_label.cget("text") == "Unauthorized Access Alarm"
        assert app.alarm_sound.active
        app.switch_mode("Moore")
        assert app.session.state == S.ALARM
        assert app.alarm_sound.active
        assert app.gate_panel.values["Alarm"].cget("text") == "ON"
        app.controls.buttons[I.AUTHORIZED_RESET].invoke()
        assert app.session.state == S.LOCKED
        assert not app.alarm_sound.active

        # Exercise native menu commands, not only their underlying callbacks.
        view_menu = app.nametowidget(app.menu_bar.entrycget(1, "menu"))
        for index, name in enumerate(("Simulator", "Transition table", "Compare machines", "Quick guide")):
            view_menu.invoke(index)
            app.update()
            assert app.view == name and app.pages[name].winfo_ismapped()
        mode_menu = app.nametowidget(app.menu_bar.entrycget(2, "menu"))
        mode_menu.invoke(1)
        assert app.session.mode == "Mealy"
        actions_menu = app.nametowidget(app.menu_bar.entrycget(3, "menu"))
        actions_menu.invoke(0)
        assert app.session.state == S.UNLOCKED

        # Keyboard activation on the CTk canvas must run the same action.
        app.show_view("Simulator")
        app.update()
        widget = app.controls.buttons[I.PUSH_GATE]
        widget._canvas.focus_force()
        app.update()
        widget._canvas.event_generate("<Return>")
        app.update()
        assert app.session.state == S.LOCKED

        # Drag the actual card onto the reader on the turnstile canvas.
        def drag_to_reader():
            canvas = app.gate_panel.drawing
            app.update()
            bounds = canvas.bbox("card")
            start_x, start_y = int((bounds[0]+bounds[2])/2), int((bounds[1]+bounds[3])/2)
            left, top, right, bottom = app.gate_panel.reader_bounds
            end_x, end_y = int((left+right)/2), int((top+bottom)/2)
            canvas.event_generate("<Motion>", x=start_x, y=start_y)
            canvas.event_generate("<ButtonPress-1>", x=start_x, y=start_y)
            app.update()
            assert app.gate_panel.dragging
            canvas.event_generate("<B1-Motion>", x=end_x, y=end_y)
            canvas.event_generate("<ButtonRelease-1>", x=end_x, y=end_y)
            app.update()
            assert not app.gate_panel.dragging and app.gate_panel.card_placed

        balance_before = app.session.card.balance
        app.set_card_status("Card blocked")
        app.gate_panel.return_card()
        drag_to_reader()
        assert app.session.state == S.LOCKED
        assert app.session.card.balance == balance_before
        app.set_card_status("Card active")
        app.gate_panel.return_card()
        drag_to_reader()
        assert app.session.state == S.UNLOCKED
        assert app.session.card.balance == balance_before-app.session.fare
        app.gate_panel.scan_button.invoke()
        assert app.session.card.balance == balance_before-app.session.fare
        app.controls.buttons[I.PUSH_GATE].invoke()
        app.gate_panel.return_card()
        assert not app.gate_panel.card_placed
        history_before = len(app.session.history)
        app.gate_panel.check_button.invoke()
        assert len(app.session.history) == history_before
        assert "Card balance" in app.gate_panel.card_feedback.cget("text")
        app.gate_panel.recharge_entry.delete(0, "end")
        app.gate_panel.recharge_entry.insert(0, "10.25")
        app.gate_panel.recharge_button.invoke()
        from decimal import Decimal
        assert app.session.card.balance == balance_before-app.session.fare+Decimal("10.25")
        app.gate_panel.recharge_entry.delete(0, "end")
        app.gate_panel.recharge_entry.insert(0, "-1")
        app.gate_panel.recharge_button.invoke()
        assert "Recharge failed" in app.gate_panel.card_feedback.cget("text")
        assert len(app.session.history) == history_before

        # Event-loop demos: preparation, cancellation and a full security sequence.
        app.run_scenario("Successful entry")
        app.stop_scenario()
        before = len(app.session.history)
        app.update()
        assert not app.scenario_running and app.scenario_id is None
        assert len(app.session.history) == before
        app.run_scenario("Unauthorized push")
        deadline = time.monotonic() + 6
        while app.scenario_running and time.monotonic() < deadline:
            app.update()
            time.sleep(.02)
        assert not app.scenario_running
        assert app.session.state == S.LOCKED
        assert [result.input for result in app.session.history[-3:]] == [I.PUSH_GATE, I.VALID_CARD, I.AUTHORIZED_RESET]
        assert not app.alarm_sound.active

        with patch("ui.main_window.filedialog.asksaveasfilename", return_value=""):
            app.export_log()  # cancellation should have no effect

        # Inspect geometry at both the default and minimum supported window size.
        for size in ("1260x900", "980x680"):
            app.geometry(size)
            app.show_view("Simulator")
            app.update()
            for gate_input, widget in app.controls.buttons.items():
                assert widget.winfo_width() >= 140, (size, gate_input)
            assert app.gate_panel.winfo_width() >= 320, size
            available_width = app.scroll._parent_canvas.winfo_width()
            required_width = app.pages["Simulator"].winfo_width()
            print(f"Available content={available_width}px, required={required_width}px")
            assert required_width <= available_width + 10, size
            print(f"Layout {size}: gate={app.gate_panel.winfo_width()}px, controls={app.controls.winfo_width()}px")
        assert not errors, errors
        print("GUI integration passed: card dragging, balance, recharge, controls, menus, outputs, keyboard, scenarios and layout. No screenshots created.")
    finally:
        app.close()


if __name__ == "__main__":
    run()
