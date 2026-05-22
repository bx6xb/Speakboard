import os
import re
import textwrap
from datetime import datetime


MAX_LINE_WIDTH = 80
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def _wrap_text(text: str) -> str:
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
            continue
        wrapped = textwrap.fill(paragraph, width=MAX_LINE_WIDTH,
                                break_long_words=False, break_on_hyphens=False)
        lines.append(wrapped)
    return "\n".join(lines)


def _last_timestamp(filepath: str) -> str | None:
    """Return the last HH:MM timestamp line found in the file, or None."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    last = None
    for line in content.splitlines():
        if _TIME_RE.match(line.strip()):
            last = line.strip()
    return last


class NotesDirNotConfigured(Exception):
    pass


def _validate_notes_dir(notes_dir: str):
    if not notes_dir or notes_dir.strip().upper() == "CHANGE_ME":
        raise NotesDirNotConfigured(
            "Notes directory is not configured.\n"
            "  Open config.json and set 'notes_dir' to a real folder path.\n"
            "  Example: \"C:/Users/YourName/Documents/Notes\""
        )


def append_note(notes_dir: str, text: str):
    _validate_notes_dir(notes_dir)
    os.makedirs(notes_dir, exist_ok=True)

    today = datetime.now()
    filename = today.strftime("%d.%m")
    filepath = os.path.join(notes_dir, filename)

    time_str = today.strftime("%H:%M")
    wrapped = _wrap_text(text)

    has_content = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    same_minute = _last_timestamp(filepath) == time_str

    with open(filepath, "a", encoding="utf-8") as f:
        if same_minute:
            # Same minute as the previous entry — append under the same timestamp
            f.write("\n")
            f.write(wrapped)
            f.write("\n")
        else:
            # New minute — write timestamp header, then text
            if has_content:
                f.write("\n")
            f.write(f"{time_str}\n")
            f.write(wrapped)
            f.write("\n")


def open_notes_folder(notes_dir: str):
    os.makedirs(notes_dir, exist_ok=True)
    os.startfile(notes_dir)
