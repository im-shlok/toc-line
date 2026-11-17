import unittest
from unittest.mock import Mock, patch
import wave

from ui.alarm_sound import AlarmSound


class AlarmSoundTests(unittest.TestCase):
    def test_windows_playback_loops_and_stops_without_blocking(self):
        root = Mock()
        audio = Mock(SND_FILENAME=1, SND_ASYNC=2, SND_LOOP=4, SND_NODEFAULT=8)
        alarm = AlarmSound(root)
        with patch("ui.alarm_sound.winsound", audio):
            alarm.set_active(True)
            audio.PlaySound.assert_called_once_with(str(alarm.path), 15)
            # Refreshes or mode switches during a latched alarm must not restart it.
            alarm.set_active(True)
            self.assertEqual(audio.PlaySound.call_count, 1)
            alarm.set_active(False)
            audio.PlaySound.assert_called_with(None, 0)
            self.assertFalse(alarm.active)
            root.bell.assert_not_called()

    def test_bell_fallback_cancels_repeat_on_reset_or_close(self):
        root = Mock()
        root.after.return_value = "repeat-id"
        alarm = AlarmSound(root)
        with patch("ui.alarm_sound.winsound", None):
            alarm.set_active(True)
            root.bell.assert_called_once()
            callback = root.after.call_args.args[1]
            callback()
            self.assertEqual(root.bell.call_count, 2)
            alarm.stop()
            root.after_cancel.assert_called_once_with("repeat-id")
            callback()  # A stale callback after shutdown must not ring again.
            self.assertEqual(root.bell.call_count, 2)

    def test_audio_failure_uses_bell_and_does_not_break_reset(self):
        root = Mock()
        audio = Mock(SND_FILENAME=1, SND_ASYNC=2, SND_LOOP=4, SND_NODEFAULT=8)
        audio.PlaySound.side_effect = RuntimeError("No audio device")
        alarm = AlarmSound(root)
        with patch("ui.alarm_sound.winsound", audio):
            alarm.set_active(True)
            root.bell.assert_called_once()
            alarm.stop()
            self.assertFalse(alarm.active)
            root.after_cancel.assert_called_once()

    def test_bundled_sound_contains_audible_pcm_samples(self):
        alarm = AlarmSound(Mock())
        with wave.open(str(alarm.path), "rb") as sound:
            self.assertEqual(sound.getnchannels(), 1)
            self.assertEqual(sound.getsampwidth(), 2)
            self.assertEqual(sound.getnframes(), sound.getframerate())
            self.assertTrue(any(sound.readframes(sound.getnframes())))


if __name__ == "__main__":
    unittest.main()
