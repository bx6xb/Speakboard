# Speakboard

> Press a hotkey. Speak. Text appears.

A lightweight Windows app that transcribes your speech using a local Whisper AI model —
no cloud, no subscription, completely offline.
It runs silently in the system tray and is controlled entirely by hotkeys.

---

## Hotkeys

| Key                     | What happens |
|-------------------------|--------------|
| Right Alt               | Start recording → press again to stop → text is copied to clipboard |
| Right Alt + Right Shift | Start recording → press again to stop → text is appended to today's notes file |

---

## Installation

> **Before you start:** make sure [Python 3.10 or newer](https://www.python.org/downloads/) is installed.
> During installation, check the box **"Add Python to PATH"**.

### 1. Download the project

Download the ZIP from GitHub (green **Code** button → **Download ZIP**),
extract it anywhere, and open a terminal inside that folder.

**How to open a terminal in the folder:**
Right-click inside the folder while holding **Shift** → choose **"Open PowerShell window here"**
(or **"Open in Terminal"** on Windows 11).

### 2. Create a virtual environment

In the terminal, run:

```bash
python -m venv venv
venv\Scripts\activate
```

After the second command, you should see `(venv)` at the start of the line —
that confirms the virtual environment is active.

> **What is a virtual environment?**
> It's a self-contained copy of Python just for this project, so nothing here
> conflicts with other programs on your computer.
> You need to activate it (`venv\Scripts\activate`) each time you open a new terminal.

### 3. Install the required libraries

```bash
pip install -r requirements.txt
```

### 4. Install PyTorch for your hardware

PyTorch is the library that lets Speakboard use your GPU for fast transcription.
The right version depends on what's in your computer — pick one row from the table:

| Your hardware | Command to run |
|---------------|----------------|
| NVIDIA RTX 50-series (5060 Ti, 5070, 5080 …) | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| NVIDIA RTX 30 or 40-series (3060, 4070 …) | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| No NVIDIA GPU / laptop without a dedicated GPU | `pip install torch` |

> **Not sure which GPU you have?**
> Press `Win + R`, type `dxdiag`, press Enter. Your GPU is listed under the **Display** tab.

After installing, verify it works:
```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```
If it prints `True` and your GPU name — you're all set.
If it prints `False` — the app will still work, just using the CPU (see **GPU vs CPU** below).

> **What is CUDA?** It's NVIDIA's technology that lets the AI model run on your
> graphics card instead of the processor — making transcription roughly real-time
> instead of several times slower.

### 5. Set up your notes folder

Copy the example settings file:

```bash
copy .env.example .env
```

Open the newly created `.env` file in any text editor (Notepad is fine) and
replace `YourName` with your actual Windows username:

```
NOTES_DIR=C:/Users/YourName/Documents/Notes
```

The folder will be created automatically when you first use Notes mode.

> If `NOTES_DIR` is not set and you try Notes mode, the overlay will show
> `⚠ Set NOTES_DIR in .env` instead of recording.

### 6. Run the app

```bash
python main.py
```

A microphone icon appears in the system tray (bottom-right corner of the taskbar).
The hotkeys are now live — you can press Right Alt at any time.

On first launch, the app registers itself to **start automatically on Windows login**,
so you won't need to run this command again after restarting your computer.

---

## GPU vs CPU — will it work on a laptop?

| Hardware | AI model used | Speed |
|----------|--------------|-------|
| NVIDIA GPU (with CUDA) | `large-v3` | ~real-time |
| CPU only (no GPU) | `medium` | 2–5× slower than recording duration |

**Example:** on a Ryzen 7 laptop without a GPU, a 10-second recording
might take 20–40 seconds to transcribe. Perfectly usable for occasional notes.
For daily heavy use, a dedicated GPU makes a noticeable difference.

---

## How autostart works

On first run, the app places a small startup file here:

```
C:\Users\YourName\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\speakboard.bat
```

Windows automatically runs everything in that Startup folder when you log in.
To **disable autostart**, just delete `speakboard.bat` from that folder.

---

## Notes file format

Notes are saved as plain text files named `DD.MM` (e.g. `22.05`) in your `NOTES_DIR` folder.
Multiple recordings in the same minute are grouped under one timestamp:

```
14:32
First entry recorded at 14:32.

Also recorded at 14:32 — grouped under the same timestamp.

17:05
New entry at a different time gets its own timestamp.
```

---

## System tray menu

Right-click the tray icon (bottom-right corner):

| Item | Action |
|------|--------|
| Open notes folder | Opens your notes folder in Explorer |
| Reload model | Reloads the AI model without restarting the app |
| Exit | Closes Speakboard |

---

## Troubleshooting

**Hotkeys don't work in some apps (browsers, games):**
Run the terminal as administrator before launching:
right-click PowerShell → *Run as administrator*, then `python main.py`.

**Hotkeys not responding at all / wrong key detected:**
Run with the debug flag to see what key names your keyboard reports:
```bash
python main.py --debug
```
Then press Right Alt and check what name appears in the console.

---

## Requirements

- Windows 10 or 11
- Python 3.10 or newer
- A microphone
- NVIDIA GPU *(optional, but strongly recommended for real-time speed)*
