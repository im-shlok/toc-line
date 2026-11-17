"""Reproduce the bundled two-tone alarm using only the Python standard library."""
import math
import struct
import wave
from pathlib import Path


def generate():
    path = Path(__file__).resolve().parents[1] / "assets" / "sounds" / "alarm.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    rate = 22050
    samples = bytearray()
    for index in range(rate):
        moment = index / rate
        frequency = 880 if moment < .2 else 1175 if .28 <= moment < .48 else 0
        start = 0 if moment < .2 else .28
        phase = moment - start
        # Brief fades remove clicks at the tone boundaries; the remainder is silence.
        envelope = max(0, min(1, phase / .01, (.2-phase) / .01)) if frequency else 0
        value = int(10000 * envelope * math.sin(2 * math.pi * frequency * phase))
        samples.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(rate)
        sound.writeframes(samples)
    print(f"Generated {path.name}: two tones, 1-second loop, mono 16-bit PCM.")


if __name__ == "__main__":
    generate()
