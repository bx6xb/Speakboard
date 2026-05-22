# Speakboard — Agent Context

Windows speech-to-text overlay app. Runs silently in the system tray, controlled
entirely by hotkeys. No window, no cloud. Transcribes via local faster-whisper model.

## File map

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point. App state machine, hotkey hook, wires everything together |
| `recorder.py` | Microphone capture via `sounddevice`. Writes temp `.wav`, exposes amplitude callback |
| `transcriber.py` | `faster-whisper` wrapper. Auto-detects CUDA/CPU, loads model once at startup |
| `overlay.py` | Tkinter floating pill UI. Runs in a daemon thread, all updates via `root.after()` |
| `notes.py` | Daily notes file logic: create/append, word-wrap at 80 chars, same-minute grouping |
| `tray.py` | `pystray` system tray icon + right-click menu |

## App state machine (main.py → class App)

```
IDLE
  → [Right Alt↓ + Right Shift state snapshotted] → Right Alt↑
       ├─ shift was held → RECORDING_NOTES
       └─ no shift      → RECORDING_PASTE
            ↓ Right Alt↑ again
       PROCESSING
            ↓ transcription done
       IDLE
```

State is protected by `_state_lock`. Recording and processing run in daemon threads.

## Hotkey implementation (critical quirk)

- Uses `keyboard.hook()` (low-level Windows hook, needs admin for some apps)
- Right Alt on non-US keyboards = AltGr → reported as `"altgr"` not `"right alt"`.
  `RALT_NAMES = {"right alt", "altgr", "alt gr", "right menu"}` covers all variants.
- Right Shift is tracked **inside the hook** as its own key event (not via `is_pressed()`
  at KEY_UP time). This handles all press-order combinations reliably.
- Run with `--debug` flag to print all key names/scan codes to console.

## Overlay (overlay.py)

- Tkinter window in a daemon thread. `overrideredirect=True`, `-topmost`, transparent background.
- All state changes go through `root.after(0, fn)` — never touch tk from another thread directly.
- Animation loop: `root.after(FPS=16ms, tick)` → ~60 fps.
- Waveform: 34 bars, Gaussian bell-curve weights (center tallest), bars lerp toward target height.
  Amplitude comes from `recorder.py` callback via `update_amplitudes(float)`.
  `AMP_SCALE=28` boosts raw int16 amplitude (typically 0.01–0.1) to visible bar heights.
- Themes: dark (`#111111` bg, white bars) for clipboard mode; light (`#f2f2f2`) for notes mode.
- States: `recording` → animated waveform | `transcribing` → 3 bouncing dots |
  `done_*` → text label, auto-hides after 2s | `no_config` → ⚠ warning on light theme.

## Configuration (.env)

Single variable: `NOTES_DIR` — absolute path to daily notes folder.
Loaded via `python-dotenv` at startup. If unset, notes mode shows overlay warning
and refuses to record (does not crash). Clipboard mode works without `.env`.

## Notes file format

- Filename: `DD.MM` (e.g. `22.05`), plain UTF-8 text.
- Same-minute grouping: `notes.py._last_timestamp()` reads last `HH:MM` line in file.
  If it matches current minute → no new timestamp header, just blank line + text.
- Word-wrap: `textwrap.fill(width=80, break_long_words=False, break_on_hyphens=False)`.

## Autostart

`setup_autostart()` in `main.py` creates `speakboard.vbs` in the Windows Startup folder.
VBS launches `pythonw.exe` (no console) with window style `0` (fully hidden).
Also cleans up old names: `stt_app.bat`, `voxdrop.bat`, `speakboard.bat`.

## Transcription

- GPU path: `large-v3`, `float16`, CUDA. Detected via `torch.cuda.is_available()`.
- CPU fallback: `medium`, `int8`. Auto-selected if no CUDA.
- `beam_size=5`, `vad_filter=True`, `language=None` (auto-detect, handles mixed Russian/English).
- Model loaded once at startup, kept in VRAM. `tray → Reload model` calls `transcriber.reload()`.

## Clipboard mode behaviour

After transcription, always `pyperclip.copy(text)`. No window detection, no auto-paste.
User pastes manually with Ctrl+V. This was a deliberate decision — auto-paste into
the focused window caused unreliable behaviour and accidental inserts.

## Key libraries

`faster-whisper`, `sounddevice`, `keyboard`, `pyperclip`, `pystray`, `Pillow`,
`python-dotenv`, `torch` (installed separately — version depends on GPU generation).

## What NOT to do

- Don't call any tkinter method from outside the tk thread — use `root.after(0, fn)`.
- Don't add auto-paste-to-window logic back — it was removed intentionally.
- Don't put personal paths in committed files — use `.env` (gitignored).
- Don't use `keyboard.wait()` as the main loop — it raises `KeyboardInterrupt` uncatchably;
  use `while True: time.sleep(0.5)` with a try/except instead.
