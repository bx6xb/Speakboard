import sounddevice as sd
import numpy as np
import wave
import tempfile
import os
import threading
from collections import deque


SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16
AMPLITUDE_WINDOW = 20  # number of recent amplitude samples for waveform


class Recorder:
    def __init__(self, on_amplitude=None):
        self._frames = []
        self._recording = False
        self._stream = None
        self._temp_file = None
        self._lock = threading.Lock()
        self.on_amplitude = on_amplitude
        self._amplitude_history = deque(maxlen=AMPLITUDE_WINDOW)

    @property
    def is_recording(self):
        return self._recording

    def get_amplitude_history(self):
        with self._lock:
            return list(self._amplitude_history)

    def start(self):
        self._frames = []
        self._recording = True

        def callback(indata, frames, time, status):
            if self._recording:
                chunk = indata.copy()
                with self._lock:
                    self._frames.append(chunk)
                    amplitude = float(np.abs(chunk).mean()) / 32768.0
                    self._amplitude_history.append(amplitude)
                if self.on_amplitude:
                    self.on_amplitude(amplitude)

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
            blocksize=1024,
        )
        self._stream.start()

    def stop(self):
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        return self._save_to_temp()

    def _save_to_temp(self):
        if not self._frames:
            return None
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        audio_data = np.concatenate(self._frames, axis=0)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        self._temp_file = tmp.name
        return tmp.name

    def cleanup(self):
        if self._temp_file and os.path.exists(self._temp_file):
            os.remove(self._temp_file)
            self._temp_file = None
