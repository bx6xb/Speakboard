import tkinter as tk
import math
import threading
import time


STATE_RECORDING    = "recording"
STATE_TRANSCRIBING = "transcribing"
STATE_DONE_PASTE   = "done_paste"
STATE_DONE_CLIP    = "done_clipboard"
STATE_DONE_NOTE    = "done_note"
STATE_NO_CONFIG    = "no_config"

THEME_PASTE = {
    "bg":      "#111111",
    "bar":     "#ffffff",
    "bar_dim": "#333333",
    "fg":      "#ffffff",
    "border":  "#2a2a2a",
}
THEME_NOTES = {
    "bg":      "#f2f2f2",
    "bar":     "#111111",
    "bar_dim": "#cccccc",
    "fg":      "#111111",
    "border":  "#d0d0d0",
}

PANEL_W  = 260
PANEL_H  = 44
RADIUS   = 22
TASKBAR_OFFSET = 20

WAVE_BARS   = 34          # fills width with only ~8px margin each side
BAR_W       = 5
BAR_GAP     = 2
BAR_MIN_H   = 2
BAR_MAX_H   = PANEL_H - 8    # 36 px — more vertical room

# Gaussian weights: tight bell so center bars are dramatically taller
def _gauss_weights(n):
    c = (n - 1) / 2
    s = n / 5.0   # narrower sigma → sharper mountain shape
    w = [math.exp(-((i - c) ** 2) / (2 * s * s)) for i in range(n)]
    return w

WAVE_WEIGHTS = _gauss_weights(WAVE_BARS)  # recomputed automatically from WAVE_BARS

AMP_EMA   = 0.40    # smoothing factor for incoming amplitude
AMP_SCALE = 28.0    # boosted for more expressive response
LERP      = 0.30    # bar height smoothing per frame

DOTS          = 3
DOT_R         = 3
DOT_SPACING   = 14
DOT_BOUNCE    = 5   # px vertical bounce

FPS       = 16      # ms per frame ≈ 60 fps
AUTO_HIDE = 2.0


class Overlay:
    def __init__(self):
        self._root    = None
        self._canvas  = None
        self._state   = None
        self._theme   = THEME_PASTE
        self._running = False
        self._lock    = threading.Lock()

        # amplitude state
        self._amp_smooth  = 0.0
        self._bar_heights = [float(BAR_MIN_H)] * WAVE_BARS

        # animation state
        self._phase   = 0.0
        self._anim_id = None
        self._hide_timer = None

        t = threading.Thread(target=self._tk_main, daemon=True)
        t.start()
        for _ in range(80):
            if self._root is not None:
                break
            time.sleep(0.05)

    # ── Tk thread ─────────────────────────────────────────────────────────────

    def _tk_main(self):
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.97)
        root.configure(bg="#010101")
        root.wm_attributes("-transparentcolor", "#010101")

        canvas = tk.Canvas(root, width=PANEL_W, height=PANEL_H,
                           bg="#010101", highlightthickness=0)
        canvas.pack()

        self._root   = root
        self._canvas = canvas
        self._running = True
        root.mainloop()

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _taskbar_h(self):
        try:
            import ctypes, ctypes.wintypes as wt
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            r = wt.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
            return ctypes.windll.user32.GetSystemMetrics(1) - r.top
        except Exception:
            return 40

    def _reposition(self):
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = (sw - PANEL_W) // 2
        y  = sh - self._taskbar_h() - PANEL_H - TASKBAR_OFFSET
        self._root.geometry(f"{PANEL_W}x{PANEL_H}+{x}+{y}")

    # ── Draw helpers ──────────────────────────────────────────────────────────

    def _pill(self, c, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r, y1,  x2-r, y1,
            x2,   y1,  x2,   y1+r,
            x2,   y2-r, x2,  y2,
            x2-r, y2,  x1+r, y2,
            x1,   y2,  x1,   y2-r,
            x1,   y1+r, x1,  y1,
        ]
        c.create_polygon(pts, smooth=True, **kw)

    # ── Frame ─────────────────────────────────────────────────────────────────

    def _draw(self):
        if not self._running or self._canvas is None:
            return
        c  = self._canvas
        th = self._theme
        c.delete("all")

        self._pill(c, 1, 1, PANEL_W-1, PANEL_H-1, RADIUS,
                   fill=th["bg"], outline=th["border"], width=1)

        cx, cy = PANEL_W // 2, PANEL_H // 2

        if self._state == STATE_RECORDING:
            self._draw_wave(c, th, cx, cy)
        elif self._state == STATE_TRANSCRIBING:
            self._draw_dots(c, th, cx, cy)
        elif self._state in (STATE_DONE_PASTE, STATE_DONE_CLIP, STATE_DONE_NOTE):
            self._draw_done(c, th, cx, cy)
        elif self._state == STATE_NO_CONFIG:
            self._draw_no_config(c, cx, cy)

    def _draw_wave(self, c, th, cx, cy):
        amp = self._amp_smooth
        total_w = WAVE_BARS * (BAR_W + BAR_GAP) - BAR_GAP
        x0 = cx - total_w // 2

        for i in range(WAVE_BARS):
            target = BAR_MIN_H + WAVE_WEIGHTS[i] * AMP_SCALE * amp * BAR_MAX_H
            target = min(target, BAR_MAX_H)

            # lerp toward target
            cur = self._bar_heights[i]
            self._bar_heights[i] = cur + (target - cur) * LERP
            h = max(BAR_MIN_H, int(self._bar_heights[i]))

            color = th["bar"] if h > BAR_MIN_H + 1 else th["bar_dim"]
            bx = x0 + i * (BAR_W + BAR_GAP)
            half = h // 2
            c.create_rectangle(bx, cy - half,
                                bx + BAR_W, cy + half,
                                fill=color, outline="")

    def _draw_dots(self, c, th, cx, cy):
        for i in range(DOTS):
            offset = math.sin(self._phase + i * (math.pi * 2 / DOTS)) * DOT_BOUNCE
            dx = cx - DOT_SPACING * (DOTS - 1) / 2 + i * DOT_SPACING
            dy = cy + offset
            c.create_oval(dx - DOT_R, dy - DOT_R,
                          dx + DOT_R, dy + DOT_R,
                          fill=th["fg"], outline="")

    def _draw_no_config(self, c, cx, cy):
        c.create_text(cx, cy, text="⚠  Set NOTES_DIR in .env",
                      fill="#111111", font=("Segoe UI", 11, "bold"),
                      anchor="center")

    def _draw_done(self, c, th, cx, cy):
        labels = {
            STATE_DONE_PASTE: "✓  Pasted",
            STATE_DONE_CLIP:  "✓  Copied to clipboard",
            STATE_DONE_NOTE:  "✓  Added to notes",
        }
        c.create_text(cx, cy, text=labels.get(self._state, "✓"),
                      fill=th["fg"], font=("Segoe UI", 11, "bold"),
                      anchor="center")

    # ── Animation loop ────────────────────────────────────────────────────────

    def _tick(self):
        if not self._running or self._state is None:
            return
        self._phase = (self._phase + 0.18) % (math.pi * 2)

        # decay amplitude when silent (no update_amplitudes calls keep it fed)
        self._amp_smooth *= 0.92

        self._draw()
        self._anim_id = self._root.after(FPS, self._tick)

    def _start_anim(self):
        if self._anim_id:
            self._root.after_cancel(self._anim_id)
            self._anim_id = None
        self._tick()

    def _stop_anim(self):
        if self._anim_id:
            self._root.after_cancel(self._anim_id)
            self._anim_id = None

    # ── Hide timer ────────────────────────────────────────────────────────────

    def _cancel_hide(self):
        if self._hide_timer:
            self._hide_timer.cancel()
            self._hide_timer = None

    def _sched_hide(self):
        self._cancel_hide()
        t = threading.Timer(AUTO_HIDE, lambda: self._root.after(0, self._do_hide))
        t.daemon = True
        t.start()
        self._hide_timer = t

    def _do_hide(self):
        self._stop_anim()
        self._state = None
        self._root.withdraw()

    # ── Public API ────────────────────────────────────────────────────────────

    def update_amplitudes(self, amplitude: float):
        """Called from audio callback thread."""
        self._amp_smooth = AMP_EMA * amplitude + (1 - AMP_EMA) * self._amp_smooth

    def show_recording(self, mode: str):
        def _go():
            self._cancel_hide()
            self._theme = THEME_PASTE if mode == "paste" else THEME_NOTES
            self._state = STATE_RECORDING
            # reset bars so they grow from zero
            self._bar_heights = [float(BAR_MIN_H)] * WAVE_BARS
            self._amp_smooth  = 0.0
            self._reposition()
            self._root.deiconify()
            self._start_anim()
        if self._root:
            self._root.after(0, _go)

    def show_transcribing(self):
        def _go():
            self._cancel_hide()
            self._state = STATE_TRANSCRIBING
            self._start_anim()
        if self._root:
            self._root.after(0, _go)

    def show_no_config(self):
        """Flash the 'configure .env' warning and auto-hide."""
        def _go():
            self._cancel_hide()
            self._theme = THEME_NOTES  # light theme for visibility
            self._stop_anim()
            self._state = STATE_NO_CONFIG
            self._reposition()
            self._root.deiconify()
            self._draw()
            self._sched_hide()
        if self._root:
            self._root.after(0, _go)

    def show_done(self, result: str):
        state_map = {
            "paste":     STATE_DONE_PASTE,
            "clipboard": STATE_DONE_CLIP,
            "note":      STATE_DONE_NOTE,
        }
        def _go():
            self._stop_anim()
            self._state = state_map.get(result, STATE_DONE_PASTE)
            self._draw()
            self._sched_hide()
        if self._root:
            self._root.after(0, _go)

    def hide(self):
        if self._root:
            self._root.after(0, self._do_hide)
