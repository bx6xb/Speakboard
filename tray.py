import threading
import pystray
from PIL import Image, ImageDraw


def _create_tray_icon_image(size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark circle background
    draw.ellipse((2, 2, size - 2, size - 2), fill=(30, 30, 46, 230))

    # Microphone body
    mx, my = size // 2, size // 2
    mic_w, mic_h = size // 5, size // 3
    draw.rounded_rectangle(
        [mx - mic_w, my - mic_h, mx + mic_w, my + mic_h // 3],
        radius=mic_w,
        fill=(137, 180, 250, 255),
    )

    # Mic stand arc (simplified as lines)
    arc_r = mic_w + 5
    draw.arc(
        [mx - arc_r, my - arc_r // 2, mx + arc_r, my + arc_r + 4],
        start=0, end=180,
        fill=(137, 180, 250, 255),
        width=3,
    )
    # Vertical line
    draw.line([mx, my + arc_r + 4, mx, my + arc_r + 10],
              fill=(137, 180, 250, 255), width=3)
    # Base line
    draw.line([mx - arc_r // 2, my + arc_r + 10, mx + arc_r // 2, my + arc_r + 10],
              fill=(137, 180, 250, 255), width=3)

    return img


class TrayIcon:
    def __init__(self, on_open_notes, on_reload_model, on_quit):
        self.on_open_notes = on_open_notes
        self.on_reload_model = on_reload_model
        self.on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        image = _create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Open notes folder", self._open_notes),
            pystray.MenuItem("Reload model", self._reload_model),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._quit),
        )
        self._icon = pystray.Icon(
            "stt_app",
            image,
            "Speech → Text",
            menu,
        )
        self._icon.run()

    def _open_notes(self, icon, item):
        if self.on_open_notes:
            self.on_open_notes()

    def _reload_model(self, icon, item):
        if self.on_reload_model:
            self.on_reload_model()

    def _quit(self, icon, item):
        icon.stop()
        if self.on_quit:
            self.on_quit()

    def stop(self):
        if self._icon:
            self._icon.stop()
