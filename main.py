"""
main.py — Entry point for the Speech-to-Text overlay app.

Hotkeys:
  Right Alt          → Paste mode (toggle recording)
  Right Alt + Shift  → Notes mode (toggle recording)

Run with --debug to print all key events and identify key names on your system.
"""

import os
import sys
import threading
import time
import ctypes

from dotenv import load_dotenv
import keyboard
import pyperclip


# Right Alt key can have different names depending on OS locale / keyboard layout.
# "altgr" is common on Windows with non-US layouts (Russian, German, etc.)
RALT_NAMES = {"right alt", "altgr", "alt gr", "right menu"}

DEBUG_KEYS = "--debug" in sys.argv

from recorder import Recorder
from transcriber import Transcriber
from overlay import Overlay
from notes import append_note, open_notes_folder, NotesDirNotConfigured
from tray import TrayIcon


# ─── State ───────────────────────────────────────────────────────────────────

class AppState:
    IDLE = "idle"
    RECORDING_PASTE = "recording_paste"
    RECORDING_NOTES = "recording_notes"
    PROCESSING = "processing"


# ─── Config ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)

    notes_dir = os.environ.get("NOTES_DIR", "").strip()

    if not notes_dir:
        print("[Config] NOTES_DIR is not set.")
        print("  Create a .env file next to main.py and add:")
        print("  NOTES_DIR=C:/Users/YourName/Documents/Notes")
        print("  (see .env.example for reference)")

    return {"notes_dir": notes_dir}


# ─── Admin check ─────────────────────────────────────────────────────────────

def _check_admin():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        print("[Warning] Running WITHOUT administrator rights.")
        print("  The keyboard library may not intercept keys in some apps.")
        print("  Run the terminal as Administrator for reliable hotkey capture.")


# ─── Autostart ───────────────────────────────────────────────────────────────

def setup_autostart():
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup",
    )
    bat_path = os.path.join(startup_dir, "stt_app.bat")
    if os.path.exists(bat_path):
        return
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    bat_content = f'@echo off\nstart "" "{python_exe}" "{script_path}"\n'
    try:
        os.makedirs(startup_dir, exist_ok=True)
        with open(bat_path, "w") as f:
            f.write(bat_content)
        print(f"[Autostart] Added to Windows startup: {bat_path}")
    except Exception as e:
        print(f"[Autostart] Error: {e}")


# ─── GPU check ────────────────────────────────────────────────────────────────

def _check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mb = torch.cuda.get_device_properties(0).total_memory // (1024 ** 2)
            print(f"[GPU] {name} — {mb} MB VRAM — CUDA active ✓")
        else:
            print("[GPU] CUDA not available — running on CPU")
    except ImportError:
        print("[GPU] torch not installed, cannot verify CUDA")


# ─── Core app ────────────────────────────────────────────────────────────────

class App:
    def __init__(self):
        self.config = load_config()
        self.state = AppState.IDLE
        self._state_lock = threading.Lock()

        self.overlay = Overlay()
        self.recorder = Recorder(on_amplitude=self._on_amplitude)
        self.transcriber = Transcriber()
        self.tray = TrayIcon(
            on_open_notes=self._open_notes,
            on_reload_model=self._reload_model,
            on_quit=self._quit,
        )

        self._ralt_pressed       = False
        self._rshift_pressed     = False  # tracked independently in the hook
        self._notes_mode_pending = False  # true if rshift was held at any point during ralt press

    def _on_amplitude(self, amp: float):
        self.overlay.update_amplitudes(amp)

    def _open_notes(self):
        open_notes_folder(self.config["notes_dir"])

    def _reload_model(self):
        threading.Thread(target=self.transcriber.reload, daemon=True).start()

    def _quit(self):
        keyboard.unhook_all()
        os._exit(0)

    # ── Hotkey handling ───────────────────────────────────────────────────────

    def _on_key_event(self, event):
        if DEBUG_KEYS:
            print(f"[KEY] name={event.name!r:20s} scan={event.scan_code:4d} type={event.event_type}")

        # Track right shift state independently — catches any press order
        if event.name == "right shift":
            if event.event_type == keyboard.KEY_DOWN:
                self._rshift_pressed = True
                if self._ralt_pressed:
                    self._notes_mode_pending = True
            else:
                self._rshift_pressed = False
            return

        if event.name not in RALT_NAMES:
            return

        if event.event_type == keyboard.KEY_DOWN:
            if not self._ralt_pressed:
                self._ralt_pressed = True
                # Also catch case where shift was already held before ralt
                self._notes_mode_pending = self._rshift_pressed
            return

        if event.event_type == keyboard.KEY_UP:
            if not self._ralt_pressed:
                return
            self._ralt_pressed = False
            notes = self._notes_mode_pending
            self._notes_mode_pending = False

            with self._state_lock:
                current = self.state
                if current == AppState.IDLE:
                    mode = "notes" if notes else "paste"
                    self.state = AppState.RECORDING_NOTES if notes else AppState.RECORDING_PASTE
                    threading.Thread(target=self._start_recording, args=(mode,), daemon=True).start()

                elif current in (AppState.RECORDING_PASTE, AppState.RECORDING_NOTES):
                    mode = "notes" if current == AppState.RECORDING_NOTES else "paste"
                    self.state = AppState.PROCESSING
                    threading.Thread(target=self._stop_and_process, args=(mode,), daemon=True).start()

    def _start_recording(self, mode: str):
        self.overlay.show_recording(mode)
        self.recorder.start()

    def _stop_and_process(self, mode: str):
        audio_path = self.recorder.stop()
        self.overlay.show_transcribing()

        try:
            if audio_path is None:
                return

            text = self.transcriber.transcribe(audio_path)
            self.recorder.cleanup()

            if not text.strip():
                self.overlay.hide()
                with self._state_lock:
                    self.state = AppState.IDLE
                return

            if mode == "paste":
                pyperclip.copy(text)
                self.overlay.show_done("clipboard")
            else:
                append_note(self.config["notes_dir"], text)
                self.overlay.show_done("note")

        except NotesDirNotConfigured as e:
            print(f"[Config] {e}")
            self.overlay.hide()
        except Exception as e:
            print(f"[Error] {e}")
            self.overlay.hide()
        finally:
            with self._state_lock:
                self.state = AppState.IDLE

    # ── Startup ───────────────────────────────────────────────────────────────

    def run(self):
        _check_admin()
        setup_autostart()

        _check_gpu()
        print("[App] Loading Whisper model...")
        self.transcriber.load()
        print("[App] Model ready.")

        self.tray.start()

        keyboard.hook(self._on_key_event)

        if DEBUG_KEYS:
            print("[DEBUG] Key debug mode enabled. Press any key...")
        print("[App] Ready.  Right Alt = record/paste  |  Right Alt + Right Shift = record/notes  |  Ctrl+C = exit")

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("[App] Exiting.")
            self._quit()


# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.run()
