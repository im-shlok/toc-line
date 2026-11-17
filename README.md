# SmartMetro

A Python desktop simulation of an intelligent metro turnstile using Mealy and Moore finite state machines.

## Run

Requires Python 3.10 or newer with Tkinter (included with the standard Windows Python installer).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

With the dependencies installed in your active Python environment, `python main.py` also works. On Linux, your distribution may require its `python3-tk` package.

## Use the simulator

- Choose **Moore** or **Mealy**. Switching models preserves gate state and history.
- Drag the visual SmartMetro card onto the highlighted **card reader on the turnstile** and release it to scan. The card stays on the machine; drag it away or choose **Return card**. **Scan card** is the equivalent button/keyboard action.
- The demo card starts with **₹100**, with a **₹20 fare**. **Check balance** displays available funds; enter a positive recharge amount and choose **Add balance**. **Card blocked** simulates an inactive card.
- Card scans, including the Valid card button and menu action, check balance before sending VALID_CARD or INVALID_CARD to the FSM. One fare is deducted only when a scan opens a locked gate. Scans while open or during an alarm never deduct again. Low balance and blocked cards are rejected without charging. Balance and recharge messages are activity events, separate from FSM outputs.
- **Valid card** opens a locked gate. **Push gate / enter** closes an open gate and counts one passenger.
- **Invalid card** leaves the current state unchanged. An invalid scan while already unlocked keeps the gate open, as specified by the transition table.
- Pushing a locked gate or detecting tailgating activates **ALARM**. Only **Reset alarm** clears it.
- A repeating two-tone sound plays throughout **ALARM** and stops on authorized reset or closing the app. Windows uses the bundled WAV asynchronously; other platforms use the system bell. System volume and audio/bell settings determine whether it is audible.
- The interactive sidebar and **View** menu open the simulator, full transition table, comparison, and guide.
- **Actions** sends any input from any page. **Scenarios** runs successful entry, unauthorized push, or tailgating demonstrations. **Escape** stops a scenario; manual input or changing mode also stops it. Scenario preparation uses normal inputs and records every action.
- **File → Export activity log** saves all session events as CSV. The on-screen log shows the most recent 300 events; export retains all events.

Keyboard: Tab navigates, Enter/Space activates action buttons, Ctrl+1/2/3 switches pages, Ctrl+E exports. The native menus are accessible with Alt.

## FSM comparison

Both models use the same 3 states, 5 inputs and 15 transition pairs.

**Mealy:** `output(previous_state, input)` returns an input-specific response before the state is updated.

**Moore:** `output(current_state)` returns persistent gate, indicator and alarm status. It is defined at startup and remains the same across self-loops. Activity events are logged separately and are not Moore outputs. Representing messages such as “Access Denied” as Moore outputs would require additional states.

The comparison page evaluates both output functions for the latest action. Physical gate status is displayed in both modes. Staff authorization, card validation and tailgating detection are simulated; no real login, payment system or hardware is connected.

## Validate

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The standard-library test suite checks all 30 model/state/input transitions, all 15 Mealy outputs, all three Moore output states, successful entry, latched alarms, mode switching, invalid inputs, passenger counts and CSV export. It also checks alarm playback, exact fare and insufficient balance, blocked cards, repeat-scan charging, recharge validation and balance checks. FSM tests run without GUI dependencies. GUI verification is available with `python tools/verify_gui.py`; it exercises real card dragging, balance controls and menus, opens the application briefly and does not create screenshots.

## Source layout

```text
main.py                 Application entry
models/                 State, input and persistent output definitions
fsm/                    Mealy, Moore, shared transition rules and session controller
ui/                     Main window, gate, controls, state map and activity panel
tests/                  Standard-library FSM validation
tools/verify_gui.py      GUI integration check
```

The application is entirely local; its activity history exists in memory until exported or the application is closed.
