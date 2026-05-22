import os
import textwrap
from datetime import datetime


MAX_LINE_WIDTH = 80


def _wrap_text(text: str) -> str:
    """Word-wrap text at MAX_LINE_WIDTH, never breaking mid-word."""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
            continue
        wrapped = textwrap.fill(paragraph, width=MAX_LINE_WIDTH, break_long_words=False, break_on_hyphens=False)
        lines.append(wrapped)
    return "\n".join(lines)


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

    file_exists = os.path.exists(filepath)
    has_content = file_exists and os.path.getsize(filepath) > 0

    with open(filepath, "a", encoding="utf-8") as f:
        if has_content:
            f.write("\n")
        f.write(f"{time_str}\n\n")
        f.write(wrapped)
        f.write("\n")


def open_notes_folder(notes_dir: str):
    os.makedirs(notes_dir, exist_ok=True)
    os.startfile(notes_dir)
