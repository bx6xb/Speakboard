# Speech → Text (STT App)

A real-time speech recognition app with a floating overlay UI.
Runs entirely in the background — controlled by hotkeys, no window to open.

---

## Hotkeys

| Key                     | Mode           | Action                                               |
|-------------------------|----------------|------------------------------------------------------|
| Right Alt               | Clipboard mode | Press to start recording, press again to stop → text copied to clipboard |
| Right Alt + Right Shift | Notes mode     | Press to start recording, press again to stop → text appended to daily notes file |

---

## Quick start

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

> Using a venv keeps project dependencies isolated and avoids conflicts with other Python projects on your system. Always activate it before running the app or installing packages.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install PyTorch (choose based on your hardware)

**torch is NOT included in requirements.txt** because the correct version depends on your GPU.

**RTX 50-series (Blackwell — 5060 Ti, 5070, 5080, 5090):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

**RTX 30/40-series:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**No GPU / CPU only:**
```bash
pip install torch
```

Verify your GPU is detected:
```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 4. Run

```bash
python main.py
```

On first launch:
- `config.json` is created with default settings
- A `.bat` file is added to the Windows Startup folder so the app starts automatically on boot

---

## GPU vs CPU — will it run on a laptop without a GPU?

**Yes.** The app detects available hardware at startup and chooses automatically:

| Hardware | Model used | Speed |
|----------|-----------|-------|
| NVIDIA GPU (CUDA) | `large-v3` | Fast — roughly real-time |
| CPU only | `medium` | Slower — ~2–5× the recording duration |

A **Ryzen 7 5850U** (or similar mid-range laptop CPU) will work fine with the `medium` model.
A 10-second recording might take 20–40 seconds to transcribe — usable, but not instant.
For daily driver use, a GPU (even a laptop GPU like 3050/4060) makes a big difference.

---

## Autostart — how it works

On the very first run, the app writes a file here:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\stt_app.bat
```

Windows runs everything in that Startup folder automatically on login. The `.bat` launches Python with `main.py` in the background. After boot, the tray icon appears and the hotkeys are live — you can press Right Alt at any time to start recording, no extra steps needed.

> If you want to disable autostart, just delete `stt_app.bat` from the Startup folder above.

---

## Changing the notes directory

Open `config.json` and edit the path:

```json
{
    "notes_dir": "C:/Users/YourName/Documents/Notes"
}
```

Restart the app after saving.

---

## Notes file format

Files are named `DD.MM` (e.g. `22.05`) and stored in the notes directory.

```
14:32

First entry text, automatically word-wrapped at 80 characters
per line, never breaking mid-word.

17:05

Second entry text.

```

---

## System tray

Right-click the tray icon:
- **Open notes folder** — opens the notes directory in Explorer
- **Reload model** — reloads the Whisper model without restarting
- **Exit** — closes the app

---

## Running as administrator

For reliable hotkey capture in all apps (browsers, games, IDEs), run the terminal as administrator before launching:

```bash
# In an admin PowerShell:
python main.py
```

To debug what key names your keyboard reports:
```bash
python main.py --debug
```

---

## System requirements

- Windows 10 / 11
- Python 3.10+
- Microphone
- NVIDIA GPU with CUDA 12.x (optional — highly recommended for speed)
