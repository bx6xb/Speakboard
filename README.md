# VoxDrop

> Press a hotkey. Speak. Text appears.

**GitHub description:** *Hotkey-driven Windows speech-to-text overlay powered by faster-whisper. Records on demand, transcribes locally on GPU, copies to clipboard or appends to daily notes — no cloud, no window, no friction.*

A lightweight Windows overlay app that transcribes your speech using a local
Whisper model — no cloud, no subscription, no latency except your own GPU.
Runs silently in the system tray and is controlled entirely by hotkeys.

---

## Hotkeys

| Key                     | Mode           | What happens                                             |
|-------------------------|----------------|----------------------------------------------------------|
| Right Alt               | Clipboard mode | Start recording → press again to stop → text copied to clipboard |
| Right Alt + Right Shift | Notes mode     | Start recording → press again to stop → text appended to today's notes file |

---

## Installation

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd voxdrop

python -m venv venv
venv\Scripts\activate
```

> A virtual environment keeps the project's dependencies isolated from the
> rest of your Python installation. Always activate it before running or
> installing anything.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install PyTorch for your hardware

`torch` is **not** in `requirements.txt` because the correct version depends on
your GPU. Pick the right command below:

| Hardware | Command |
|----------|---------|
| RTX 50-series (5060 Ti, 5070 …) | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| RTX 30/40-series | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| No GPU / CPU only | `pip install torch` |

Verify your GPU is detected:
```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

If CUDA is unavailable, the app automatically falls back to the `medium` model on CPU.

### 4. Configure your environment

Copy the example file and fill in your path:

```bash
copy .env.example .env
```

Open `.env` and set your notes directory:

```env
NOTES_DIR=C:/Users/YourName/Documents/Notes
```

> **Notes mode won't start recording until `NOTES_DIR` is set.** If it's missing,
> the overlay will flash `⚠ Set NOTES_DIR in .env` instead of recording.

The folder is created automatically if it doesn't exist.
`.env` is in `.gitignore` — your personal path never ends up in the repository.

### 5. Run

```bash
python main.py
```

On first launch, a `.bat` file is added to the Windows Startup folder so the
app starts automatically on every login.

---

## GPU vs CPU

| Hardware | Model | Speed |
|----------|-------|-------|
| NVIDIA GPU (CUDA) | `large-v3` | ~real-time |
| CPU only | `medium` | 2–5× the recording duration |

A **Ryzen 7 5850U** (or similar mid-range laptop CPU) will work fine with the
`medium` model — a 10-second clip might take 20–40 seconds to transcribe.
For daily use, even a laptop GPU (RTX 3050/4060) makes a big difference.

---

## How autostart works

On first run, the app writes:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\voxdrop.bat
```

Windows runs everything in that folder on login. After boot, the tray icon
appears silently and the hotkeys are immediately live — press Right Alt any time.

To disable autostart, delete `voxdrop.bat` from the Startup folder above.

---

## Notes file format

Files are named `DD.MM` (e.g. `22.05`) and stored in the `NOTES_DIR` folder.

```
14:32

First entry, automatically word-wrapped at 80 characters per line
without ever breaking mid-word.

17:05

Second entry.

```

---

## System tray

Right-click the tray icon:

| Item | Action |
|------|--------|
| Open notes folder | Opens `NOTES_DIR` in Explorer |
| Reload model | Reloads the Whisper model without restarting the app |
| Exit | Closes the app |

---

## Tips

**Run as administrator** for reliable hotkey capture across all apps (browsers,
games, elevated processes):
```bash
# In an admin PowerShell:
python main.py
```

**Debug key names** if hotkeys aren't working (useful for non-US keyboard layouts):
```bash
python main.py --debug
```

---

## Requirements

- Windows 10 / 11
- Python 3.10+
- Microphone
- NVIDIA GPU with CUDA 12.x *(optional — strongly recommended)*
