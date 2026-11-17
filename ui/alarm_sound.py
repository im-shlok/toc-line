"""Non-blocking alarm playback that follows the gate's persistent alarm status."""
from pathlib import Path
import tkinter as tk

try:
    import winsound
except ImportError:  # Standard-library Windows audio; Tk bell on other platforms.
    winsound = None


class AlarmSound:
    def __init__(self, root):
        self.root = root
        self.active = False
        self._playing = False
        self._bell_id = None
        self.path = Path(__file__).resolve().parents[1] / "assets" / "sounds" / "alarm.wav"

    def set_active(self, active: bool):
        if active == self.active:
            return
        if not active:
            self.stop()
            return
        self.active = True
        if winsound is not None and self.path.is_file():
            try:
                winsound.PlaySound(str(self.path), winsound.SND_FILENAME | winsound.SND_ASYNC
                                   | winsound.SND_LOOP | winsound.SND_NODEFAULT)
            except (OSError, RuntimeError):
                pass  # Keep the security controls usable if audio is unavailable.
            else:
                self._playing = True
                return
        self._ring_bell()

    def _ring_bell(self):
        self._bell_id = None
        if self.active:
            self.root.bell()
            self._bell_id = self.root.after(1000, self._ring_bell)

    def stop(self):
        self.active = False
        if self._bell_id is not None:
            try:
                self.root.after_cancel(self._bell_id)
            except tk.TclError:
                pass  # The window may already have been destroyed.
            self._bell_id = None
        if self._playing:
            try:
                winsound.PlaySound(None, 0)
            except (OSError, RuntimeError):
                pass
            self._playing = False
