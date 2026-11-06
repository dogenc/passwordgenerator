"""PWGen · DGKN@Labs — glass UI and application wiring."""

from __future__ import annotations

import os
import sys
import tkinter as tk
import tkinter.font as tkfont
import traceback
from tkinter import messagebox
from typing import Callable

from . import core, theme, widgets
from .widgets import (
    Button,
    GlassPanel,
    IconButton,
    Meter,
    Pill,
    ScrollArea,
    Segmented,
    Slider,
    ToggleRow,
    draw_glyph,
    measure,
    rounded,
)

USAGE = """PWGen · DGKN@Labs

Aufruf:
  pwgen_gui.py                Anwendung starten
  pwgen_gui.py --self-test    Krypto-Kern prüfen (Exitcode 0 = OK)
  pwgen_gui.py --smoke-ui     Oberfläche aufbauen und beenden
  pwgen_gui.py --version      Version ausgeben
"""


def asset_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


# --------------------------------------------------------------------------
# Small composite widgets
# --------------------------------------------------------------------------


class TabButton(tk.Canvas):
    def __init__(self, master: tk.Misc, text: str, command: Callable[[], None],
                 fonts: theme.Fonts, bg: str) -> None:
        self._text = text
        self._command = command
        self._font = fonts.ui(11, "bold")
        self._active = False
        self._hover = False
        width = measure(self._font, text) + 30
        super().__init__(master, width=width, height=34, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=1)
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<Button-1>", lambda _e: self._command())
        self.bind("<Return>", lambda _e: self._command())
        self.bind("<space>", lambda _e: self._command())
        self._redraw()

    def set_active(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        self._redraw()

    def _set_hover(self, hover: bool) -> None:
        self._hover = hover
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        width = int(self["width"])
        color = theme.TEXT if self._active else (theme.MUTED if self._hover else theme.DIM)
        self.create_text(width / 2, 12, text=self._text, fill=color,
                         font=self._font)
        if self._active:
            self.create_line(4, 30, width - 4, 30,
                             fill=theme.ACCENT, width=2, capstyle="round")


class PasswordCard(tk.Frame):
    def __init__(self, master: tk.Misc, index: int, password: str, bits: float,
                 rating: core.Rating, masked: bool,
                 on_copy: Callable[[int], None],
                 on_select: Callable[[int], None],
                 fonts: theme.Fonts, bg: str) -> None:
        super().__init__(master, bg=bg, height=104)
        self.pack_propagate(False)
        self.index = index
        self._selected = False
        self._on_select = on_select

        self.panel = GlassPanel(self, pad=13, radius=theme.CARD_RADIUS,
                                top=theme.CARD_TOP, bottom=theme.CARD_BOTTOM,
                                border=theme.BORDER, bg=bg)
        self.panel.pack(fill="both", expand=True)
        body = self.panel.body
        body.grid_columnconfigure(1, weight=1)

        self._index_label = tk.Label(
            body, text=f"{index + 1:02d}", bg=theme.CARD_BOTTOM, fg=theme.DIM,
            font=fonts.mono(11, "bold"),
        )
        self._index_label.grid(row=0, column=0, rowspan=2, sticky="nw",
                               padx=(2, 14), pady=(1, 0))

        display = core.masked(password) if masked else password
        self._password_label = tk.Label(
            body, text=display, bg=theme.CARD_BOTTOM, fg=theme.TEXT,
            font=fonts.mono(15), anchor="w", justify="left",
        )
        self._password_label.grid(row=0, column=1, sticky="ew")

        meta = tk.Frame(body, bg=theme.CARD_BOTTOM)
        meta.grid(row=1, column=1, sticky="w", pady=(3, 0))
        tk.Label(meta, text=core.format_bits(bits), bg=theme.CARD_BOTTOM,
                 fg=theme.MUTED, font=fonts.mono(10)).pack(side="left")
        tk.Label(meta, text="·", bg=theme.CARD_BOTTOM, fg=theme.DIM,
                 font=fonts.ui(10)).pack(side="left", padx=6)
        tk.Label(meta, text=f"{len(password)} Zeichen", bg=theme.CARD_BOTTOM,
                 fg=theme.DIM, font=fonts.ui(10)).pack(side="left")
        Pill(meta, rating.label, rating.tone, bg=theme.CARD_BOTTOM,
             font=fonts.ui(9, "bold")).pack(side="left", padx=(10, 0))

        self._copy = IconButton(body, "copy", lambda: on_copy(index),
                                size=30, bg=theme.CARD_BOTTOM, tone=theme.MUTED)
        self._copy.grid(row=0, column=2, rowspan=2, sticky="ne", padx=(10, 0))

        self._meter = Meter(body, bg=theme.CARD_BOTTOM, height=4)
        self._meter.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(9, 0))
        self._meter.set(min(1.0, bits / 160.0), rating.tone)

        for widget in (body, self._password_label, meta, self._index_label,
                       self.panel.canvas):
            widget.bind("<Button-1>", lambda _e: self._on_select(self.index))
        for widget in (self.panel.canvas, body, self._password_label, meta):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._on_configure)
        self._apply_border()

    def _on_configure(self, event: tk.Event) -> None:
        self._password_label.configure(wraplength=max(200, event.width - 150))

    def _on_enter(self, _event: tk.Event) -> None:
        if not self._selected:
            self.panel.set_border(theme.BORDER_STRONG)

    def _on_leave(self, _event: tk.Event) -> None:
        if not self._selected:
            self.panel.set_border(theme.BORDER)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._index_label.configure(fg=theme.ACCENT if selected else theme.DIM)
        self._apply_border()

    def _apply_border(self) -> None:
        self.panel.set_border(
            theme.ACCENT_SOFT if self._selected else theme.BORDER
        )


class AttackTable(tk.Frame):
    """Compact mapping of entropy to average guess time per attacker model."""

    def __init__(self, master: tk.Misc, fonts: theme.Fonts, bg: str) -> None:
        super().__init__(master, bg=bg)
        self.grid_columnconfigure(1, weight=1)
        self._values: list[tk.Label] = []
        for row, profile in enumerate(core.PROFILES):
            self.grid_rowconfigure(row, minsize=26)
            tk.Label(self, text=profile.label, bg=bg, fg=theme.MUTED,
                     font=fonts.ui(11), anchor="w").grid(
                row=row, column=0, sticky="w"
            )
            value = tk.Label(self, text="—", bg=bg, fg=theme.TEXT,
                             font=fonts.mono(11), anchor="e")
            value.grid(row=row, column=1, sticky="e")
            self._values.append(value)

    def set_bits(self, bits: float, known: bool = True) -> None:
        for profile, label in zip(core.PROFILES, self._values):
            show = known
            label.configure(
                text=core.format_crack_time(bits, profile.rate) if show else "—",
                fg=theme.TEXT if show else theme.DIM,
            )


# --------------------------------------------------------------------------
# Application
# --------------------------------------------------------------------------

METHOD_TEXT: tuple[tuple[str, str], ...] = (
    ("h", "ERZEUGUNG"),
    ("p", "Passwörter stammen aus secrets.SystemRandom, also aus dem "
          "Kryptografie-Zufallsgenerator des Betriebssystems. Ist die "
          "Klassenpflicht aktiv, werden Kandidaten verworfen und neu gezogen, "
          "bis jede gewählte Zeichenklasse mindestens einmal vorkommt. Die "
          "Verteilung bleibt dabei gleichmäßig über genau diese Menge."),
    ("h", "ENTROPIE"),
    ("p", "Angezeigt wird die exakte Entropie des erzeugbaren Schlüsselraums "
          "(Inklusion-Exklusion über die Zeichenklassen), nicht die übliche "
          "Näherung Länge × log2(Alphabet). Die Klassenpflicht senkt die "
          "Entropie leicht; genau dieser Wert wird angezeigt."),
    ("h", "ANGREIFERMODELL"),
    ("p", "Mittlere Trefferzeit = 2^(H−1) / Rate. Die Raten sind bewusst "
          "konservativ gewählt: 10/s (Login mit Sperre), 1 000/s (API ohne "
          "Sperre), 10 000/s (Argon2id/bcrypt), 10¹²/s (schneller Hash, "
          "GPU-Cluster) und 10¹⁵/s (Rechenzentrum). Die Tabelle zeigt den "
          "Mittelwert, nicht den Worst Case."),
    ("h", "PRÜFSTAND"),
    ("p", "Der Prüfstand schätzt den Zeichenvorrat, multipliziert mit der "
          "Länge und zieht Punkte für Muster ab: Wiederholungen, Sequenzen, "
          "Tastaturreihen, Jahreszahlen und Treffer in einer kleinen Liste "
          "gängiger Passwörter. Das Ergebnis ist eine Obergrenze. Es erkennt "
          "keine Leaks, keine Wiederverwendung und keine Phishing-Angriffe."),
    ("h", "DATEN UND ZWISCHENABLAGE"),
    ("p", "Kein Netzwerk. Keine Dateien. Keine Protokolle. Kopierte "
          "Passwörter werden nach der gewählten Zeit aus der Zwischenablage "
          "entfernt, sofern sie noch den kopierten Wert enthält. Python kann "
          "Strings nicht zuverlässig überschreiben; das ist eine Eigenschaft "
          "der Laufzeit und keine Zusage dieses Programms."),
    ("h", "TASTENKÜRZEL"),
    ("p", "Strg + G   erzeugen\n"
          "Strg + C   ausgewähltes Passwort kopieren\n"
          "Strg + Umschalt + C   alle kopieren\n"
          "Strg + H   Sichtschutz umschalten\n"
          "F1   Methodik   ·   Esc   Dialog schließen"),
    ("h", "LIZENZ"),
    ("p", "MIT-Lizenz · © Dogukan S. · DGKN@Labs\n"
          "Diese Anwendung ist ein Werkzeug, keine Garantie für Sicherheit. "
          "Verwenden Sie einen Passwortmanager und Zwei-Faktor-Authentifizierung."),
)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PWGen · DGKN@Labs")
        self.configure(bg=theme.BG)
        self.geometry("1200x880")
        self.minsize(1120, 820)
        self.report_callback_exception = self._on_unexpected_error

        self.fonts = theme.load_fonts(self)
        self.policy = core.build_policy(length=20)
        self._length = 20
        self._count = 1
        self._passwords: list[str] = []
        self._cards: list[PasswordCard] = []
        self._selected = 0
        self._masked = False
        self._clip_seconds = 30
        self._clip_text: str | None = None
        self._clip_job: str | None = None
        self._feedback_job: str | None = None
        self._audit_job: str | None = None
        self._status_text = "BEREIT"
        self._status_tone = "muted"
        self._info_window: tk.Toplevel | None = None
        self._view = "generator"

        self._set_window_icon()
        self._build_shell()
        self._build_generator()
        self._build_audit()
        self._show_view("generator")
        self._bind_keys()
        self._refresh_policy()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(30, self._enable_dark_titlebar)
        self.after(80, self._draw_header)
        self.after(80, self._draw_status)

    # ------------------------------------------------------------------
    # Shell
    # ------------------------------------------------------------------

    def _set_window_icon(self) -> None:
        try:
            icon = asset_path("pwgen.png")
            if os.path.exists(icon):
                self._icon_image = tk.PhotoImage(file=icon)
                self.iconphoto(True, self._icon_image)
            ico = asset_path("pwgen.ico")
            if sys.platform == "win32" and os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

    def _enable_dark_titlebar(self) -> None:
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    def _build_shell(self) -> None:
        self.header = tk.Canvas(self, height=theme.HEADER_H, bg=theme.BG,
                                highlightthickness=0, bd=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", lambda _e: self._draw_header())

        self._tab_buttons: dict[str, TabButton] = {}
        self._tab_windows: dict[str, int] = {}
        for key, label in (("generator", "GENERATOR"), ("audit", "PRÜFSTAND")):
            button = TabButton(self.header, label,
                               lambda k=key: self._show_view(k),
                               self.fonts, theme.BG)
            self._tab_buttons[key] = button
            self._tab_windows[key] = self.header.create_window(
                0, 0, anchor="sw", window=button
            )

        self._method_button = Button(
            self.header, "METHODIK", self.show_method, variant="subtle",
            height=28, font=self.fonts.ui(10, "bold"), bg=theme.BG,
        )
        self._method_window = self.header.create_window(
            0, 0, anchor="se", window=self._method_button
        )

        self.page = tk.Frame(self, bg=theme.BG)
        self.page.pack(fill="both", expand=True, padx=theme.PAGE_PAD,
                       pady=(16, 0))

        self.status = tk.Canvas(self, height=theme.STATUS_H, bg=theme.BG,
                                highlightthickness=0, bd=0)
        self.status.pack(fill="x")
        self.status.bind("<Configure>", lambda _e: self._draw_status())

    def _glow(self, canvas: tk.Canvas, cx: float, cy: float, rx: float,
              ry: float, color: str, strength: float, steps: int = 24) -> None:
        for index in range(steps, 0, -1):
            ratio = index / steps
            tint = theme.blend(color, strength * (1 - ratio) ** 2 + 0.004, theme.BG)
            canvas.create_oval(cx - rx * ratio, cy - ry * ratio,
                               cx + rx * ratio, cy + ry * ratio,
                               fill=tint, outline="", tags="art")

    def _chip(self, canvas: tk.Canvas, right: float, y: float, text: str,
              tone: str, dot: bool) -> float:
        font = self.fonts.ui(9, "bold")
        color = theme.tone(tone)
        height = 24
        width = measure(font, text) + (30 if dot else 20)
        x0 = right - width
        rounded(canvas, x0, y, right, y + height, height / 2,
                fill=theme.blend(color, 0.08, theme.BG),
                outline=theme.blend(color, 0.22, theme.BG), width=1, tags="art")
        text_x = x0 + 10
        if dot:
            canvas.create_oval(x0 + 9, y + height / 2 - 2.5, x0 + 14,
                               y + height / 2 + 2.5, fill=color, outline="",
                               tags="art")
            text_x = x0 + 19
        canvas.create_text(text_x, y + height / 2 - 1, text=text,
                           anchor="w", fill=color, font=font, tags="art")
        return width

    def _draw_header(self) -> None:
        canvas = self.header
        width = max(canvas.winfo_width(), 600)
        height = theme.HEADER_H
        canvas.delete("art")
        steps = 18
        for index in range(steps):
            y0 = height * index / steps
            y1 = height * (index + 1) / steps
            canvas.create_rectangle(0, y0, width, y1 + 1, outline="",
                                    fill=theme.mix(theme.BG_RAISED, theme.BG,
                                                   index / (steps - 1)),
                                    tags="art")
        self._glow(canvas, 90, 44, 300, 150, theme.ACCENT, 0.10)
        self._glow(canvas, width - 200, -20, 320, 150, theme.ACCENT_2, 0.09)

        left = theme.PAGE_PAD
        rounded(canvas, left, 22, left + 38, 60, 11,
                fill=theme.blend(theme.ACCENT, 0.10, theme.BG),
                outline=theme.blend(theme.ACCENT, 0.32, theme.BG),
                width=1, tags="art")
        draw_glyph(canvas, "shield", left + 19, 41, 21, theme.ACCENT,
                   width=1.5, tags="art")

        wordmark_font = self.fonts.ui(19, "bold")
        text_x = left + 52
        canvas.create_text(text_x, 33, text="DGKN", anchor="w",
                           fill=theme.TEXT, font=wordmark_font, tags="art")
        canvas.create_text(text_x + measure(wordmark_font, "DGKN"), 33,
                           text="@Labs", anchor="w", fill=theme.ACCENT,
                           font=wordmark_font, tags="art")
        canvas.create_text(text_x, 54,
                           text="PWGEN 2.0  ·  SECURE CREDENTIAL SUITE",
                           anchor="w", fill=theme.DIM,
                           font=self.fonts.ui(9, "bold"), tags="art")

        chip_y = 22
        right = width - theme.PAGE_PAD
        for text, tone, dot in (
            (f"v{core.APP_VERSION}", "muted", False),
            ("CSPRNG", "accent", True),
            ("OFFLINE", "ok", True),
        ):
            chip_width = self._chip(canvas, right, chip_y, text, tone, dot)
            right -= chip_width + 8

        canvas.create_line(0, height - 1, width, height - 1,
                           fill=theme.HAIRLINE, tags="art")
        canvas.tag_lower("art")

        offset = theme.PAGE_PAD
        for key in ("generator", "audit"):
            button = self._tab_buttons[key]
            canvas.coords(self._tab_windows[key], offset, height - 8)
            offset += int(button["width"]) + 6
        canvas.coords(self._method_window, width - theme.PAGE_PAD, height - 12)

    def _draw_status(self) -> None:
        canvas = self.status
        width = max(canvas.winfo_width(), 600)
        height = theme.STATUS_H
        canvas.delete("all")
        canvas.create_line(0, 0, width, 0, fill=theme.HAIRLINE)
        canvas.create_oval(theme.PAGE_PAD, height / 2 - 2.5,
                           theme.PAGE_PAD + 5, height / 2 + 2.5,
                           fill=theme.ACCENT, outline="")
        canvas.create_text(theme.PAGE_PAD + 12, height / 2 - 1,
                           text="OFFLINE  ·  OS-CSPRNG  ·  KEINE SPEICHERUNG",
                           anchor="w", fill=theme.DIM,
                           font=self.fonts.ui(9, "bold"))
        canvas.create_text(width - theme.PAGE_PAD, height / 2 - 1,
                           text=self._status_text, anchor="e",
                           fill=theme.tone(self._status_tone),
                           font=self.fonts.ui(10, "bold"))

    def _feedback(self, text: str, tone: str = "muted",
                  reset_after: int = 7000) -> None:
        self._status_text = text
        self._status_tone = tone
        self._draw_status()
        if self._feedback_job:
            self.after_cancel(self._feedback_job)
        self._feedback_job = self.after(reset_after, self._reset_feedback)

    def _reset_feedback(self) -> None:
        self._feedback_job = None
        self._status_text = "BEREIT"
        self._status_tone = "muted"
        self._draw_status()

    # ------------------------------------------------------------------
    # Generator view
    # ------------------------------------------------------------------

    def _build_generator(self) -> None:
        self.generator_view = tk.Frame(self.page, bg=theme.BG)

        left = tk.Frame(self.generator_view, bg=theme.BG, width=372)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.controls_panel = GlassPanel(left, pad=18)
        self.controls_panel.pack(fill="both", expand=True)
        form = self.controls_panel.body

        title_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        title_row.pack(fill="x")
        tk.Label(title_row, text="KONFIGURATION", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")
        tk.Label(title_row, text="LIVE", bg=theme.GLASS_BOTTOM,
                 fg=theme.ACCENT, font=self.fonts.ui(9, "bold")).pack(side="right")

        pad = tk.Frame(form, bg=theme.GLASS_BOTTOM, height=12)
        pad.pack(fill="x")

        length_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        length_row.pack(fill="x")
        tk.Label(length_row, text="PASSWORTLÄNGE", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")

        value_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        value_row.pack(fill="x", pady=(2, 0))
        self._length_label = tk.Label(
            value_row, text="20", bg=theme.GLASS_BOTTOM, fg=theme.TEXT,
            font=self.fonts.display(40),
        )
        self._length_label.pack(side="left")
        tk.Label(value_row, text="ZEICHEN", bg=theme.GLASS_BOTTOM,
                 fg=theme.DIM, font=self.fonts.ui(9, "bold")).pack(
            side="left", padx=(10, 0), pady=(14, 0)
        )

        self._length_slider = Slider(
            form, minimum=core.MIN_LENGTH, maximum=128, value=self._length,
            on_change=self._on_length_change, bg=theme.GLASS_BOTTOM,
        )
        self._length_slider.pack(fill="x")

        presets = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        presets.pack(fill="x", pady=(2, 4))
        for preset in (16, 24, 32, 48):
            Button(presets, str(preset), lambda value=preset: self._set_length(value),
                   variant="subtle", height=26, width=58,
                   font=self.fonts.ui(10, "bold"), bg=theme.GLASS_BOTTOM).pack(
                side="left", padx=(0, 6)
            )
        tk.Label(presets, text="SCHNELLWAHL", bg=theme.GLASS_BOTTOM,
                 fg=theme.DIM, font=self.fonts.ui(9, "bold")).pack(
            side="right", pady=(6, 0)
        )

        widgets.divider(form, pady=6)

        classes_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        classes_row.pack(fill="x", pady=(6, 4))
        tk.Label(classes_row, text="ZEICHENKLASSEN", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")
        self._alphabet_label = tk.Label(classes_row, text="", bg=theme.GLASS_BOTTOM,
                                        fg=theme.DIM, font=self.fonts.ui(9, "bold"))
        self._alphabet_label.pack(side="right")

        self._toggles: dict[str, ToggleRow] = {}
        definitions = (
            ("lower", "Kleinbuchstaben", "a – z"),
            ("upper", "Großbuchstaben", "A – Z"),
            ("digits", "Ziffern", "0 – 9"),
            ("symbols", "Sonderzeichen", "! @ # $ %"),
        )
        for key, label, subtitle in definitions:
            row = ToggleRow(form, label, subtitle, value=True,
                            fonts=self.fonts, bg=theme.GLASS_BOTTOM,
                            title_size=12)
            row.set_callback(self._on_policy_toggle)
            row.switch.bind("<ButtonRelease-1>", lambda _e: self.after(180, self._refresh_policy), add="+")
            row.pack(fill="x", pady=3)
            self._toggles[key] = row

        widgets.divider(form, pady=6)

        options_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        options_row.pack(fill="x", pady=(6, 4))
        tk.Label(options_row, text="OPTIONEN", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")

        self._ambiguous_toggle = ToggleRow(
            form, "Ambige Zeichen ausschließen", "O 0 o I l 1 | ` ' \" …",
            value=True, fonts=self.fonts, bg=theme.GLASS_BOTTOM, title_size=12,
        )
        self._ambiguous_toggle.set_callback(self._on_policy_toggle)
        self._ambiguous_toggle.pack(fill="x", pady=3)

        self._mask_toggle = ToggleRow(
            form, "Sichtschutz", "Nur Anfang und Ende anzeigen",
            value=False, fonts=self.fonts, bg=theme.GLASS_BOTTOM, title_size=12,
        )
        self._mask_toggle.set_callback(self._on_mask_toggle)
        self._mask_toggle.pack(fill="x", pady=3)

        clipboard_row = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        clipboard_row.pack(fill="x", pady=(8, 0))
        tk.Label(clipboard_row, text="ZWISCHENABLAGE", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(
            side="left", pady=(6, 0)
        )
        self._clipboard_segment = Segmented(
            clipboard_row,
            (("15", "15 s"), ("30", "30 s"), ("60", "60 s"), ("0", "Aus")),
            "30", self._on_clipboard_change, bg=theme.GLASS_BOTTOM,
            font=self.fonts.ui(9, "bold"), height=28, width=188,
        )
        self._clipboard_segment.pack(side="right")

        spacer = tk.Frame(form, bg=theme.GLASS_BOTTOM)
        spacer.pack(fill="both", expand=True)

        self._summary_label = tk.Label(
            form, text="", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
            font=self.fonts.mono(10), anchor="w",
        )
        self._summary_label.pack(fill="x", pady=(8, 6))

        self._generate_button = Button(
            form, "PASSWORT ERZEUGEN", self.generate, variant="primary",
            height=46, width=336, font=self.fonts.ui(12, "bold"),
            bg=theme.GLASS_BOTTOM, icon="key",
        )
        self._generate_button.pack(fill="x")

        # -- results column ------------------------------------------------
        right = tk.Frame(self.generator_view, bg=theme.BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))

        head = tk.Frame(right, bg=theme.BG, height=32)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text="AUSGABE", bg=theme.BG, fg=theme.MUTED,
                 font=self.fonts.ui(9, "bold")).pack(side="left", pady=(6, 0))
        self._results_subtitle = tk.Label(head, text="0 SCHLÜSSEL", bg=theme.BG,
                                          fg=theme.DIM, font=self.fonts.ui(9, "bold"))
        self._results_subtitle.pack(side="left", padx=(10, 0), pady=(6, 0))

        Button(head, "KOPIEREN", self.copy_all, variant="subtle",
               height=28, font=self.fonts.ui(9, "bold"), bg=theme.BG,
               icon="copy").pack(side="right", pady=(2, 0))
        self._count_segment = Segmented(
            head, (("1", "1"), ("3", "3"), ("5", "5")), "1",
            self._on_count_change, bg=theme.BG, font=self.fonts.ui(9, "bold"),
            height=28, width=96,
        )
        self._count_segment.pack(side="right", padx=(0, 10), pady=(2, 0))

        self._results_scroll = ScrollArea(right, bg=theme.BG)
        self._results_scroll.pack(fill="both", expand=True, pady=(10, 12))
        self._results_scroll.inner.grid_columnconfigure(0, weight=1)

        self._empty_state = tk.Frame(self._results_scroll.inner, bg=theme.BG)
        glyph = tk.Canvas(self._empty_state, width=52, height=52, bg=theme.BG,
                          highlightthickness=0)
        draw_glyph(glyph, "lock", 26, 26, 26, theme.DIM)
        glyph.pack(pady=(0, 10))
        tk.Label(self._empty_state, text="NOCH KEINE AUSGABE", bg=theme.BG,
                 fg=theme.MUTED, font=self.fonts.ui(11, "bold")).pack()
        tk.Label(self._empty_state,
                 text="Konfigurieren und mit STRG + G erzeugen.",
                 bg=theme.BG, fg=theme.DIM, font=self.fonts.ui(10)).pack(
            pady=(4, 0)
        )
        self._empty_state.pack(pady=64)

        self._cards_host = tk.Frame(self._results_scroll.inner, bg=theme.BG)
        self._cards_host.grid_columnconfigure(0, weight=1)

        self.attack_panel = GlassPanel(right, pad=16, height=212)
        self.attack_panel.pack(fill="x")
        self.attack_panel.pack_propagate(False)
        attack_body = self.attack_panel.body
        attack_head = tk.Frame(attack_body, bg=theme.GLASS_BOTTOM)
        attack_head.pack(fill="x")
        tk.Label(attack_head, text="ANGRIFFSMODELL", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")
        tk.Label(attack_head, text="MITTLERE TREFFERZEIT", bg=theme.GLASS_BOTTOM,
                 fg=theme.DIM, font=self.fonts.ui(9, "bold")).pack(side="right")
        self.attack_table = AttackTable(attack_body, self.fonts, theme.GLASS_BOTTOM)
        self.attack_table.pack(fill="x", pady=(8, 4))
        tk.Frame(attack_body, bg=theme.HAIRLINE, height=1).pack(fill="x", pady=(2, 8))
        tk.Label(
            attack_body,
            text="2^(H−1) / Rate  ·  H = exakte Policy-Entropie  ·  Raten: 10 · 10³ · 10⁴ · 10¹² · 10¹⁵ /s",
            bg=theme.GLASS_BOTTOM, fg=theme.DIM, font=self.fonts.ui(9),
            anchor="w",
        ).pack(fill="x")

    # ------------------------------------------------------------------
    # Audit view
    # ------------------------------------------------------------------

    def _build_audit(self) -> None:
        self.audit_view = tk.Frame(self.page, bg=theme.BG)

        left = tk.Frame(self.audit_view, bg=theme.BG, width=430)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        panel = GlassPanel(left, pad=20)
        panel.pack(fill="both", expand=True)
        body = panel.body

        tk.Label(body, text="PRÜFSTAND", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
                 font=self.fonts.ui(9, "bold"), anchor="w").pack(fill="x")
        tk.Label(
            body,
            text="Bestehendes Passwort analysieren. Die Bewertung beschreibt "
                 "die Obergrenze des Zeichenvorrats und erkennt strukturelle "
                 "Muster — lokal und ohne Übertragung.",
            bg=theme.GLASS_BOTTOM, fg=theme.MUTED, font=self.fonts.ui(11),
            wraplength=350, justify="left", anchor="w",
        ).pack(fill="x", pady=(6, 14))

        self._audit_entry = widgets.EntryField(
            body, show="•", height=46, bg=theme.GLASS_BOTTOM,
            font=self.fonts.mono(14), on_change=self._on_audit_change,
            on_submit=self._refresh_audit,
        )
        self._audit_entry.pack(fill="x")

        self._audit_show_toggle = ToggleRow(
            body, "Passwort anzeigen", "Sichtbar nur in diesem Fenster",
            value=False, fonts=self.fonts, bg=theme.GLASS_BOTTOM, title_size=12,
        )
        self._audit_show_toggle.set_callback(self._on_audit_show)
        self._audit_show_toggle.pack(fill="x", pady=(10, 4))

        self._audit_copy_button = Button(
            body, "IN ZWISCHENABLAGE KOPIEREN", self._copy_audit,
            variant="subtle", height=34, font=self.fonts.ui(10, "bold"),
            bg=theme.GLASS_BOTTOM, icon="copy",
        )
        self._audit_copy_button.pack(fill="x", pady=(4, 12))

        widgets.divider(body, pady=6)

        tk.Label(body, text="RICHTLINIEN", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
                 font=self.fonts.ui(9, "bold"), anchor="w").pack(fill="x",
                                                                 pady=(8, 6))
        self._requirement_rows: list[tuple[tk.Canvas, tk.Label]] = []
        for _ in range(5):
            row = tk.Frame(body, bg=theme.GLASS_BOTTOM)
            row.pack(fill="x", pady=3)
            dot = tk.Canvas(row, width=12, height=12, bg=theme.GLASS_BOTTOM,
                            highlightthickness=0)
            dot.pack(side="left", pady=(2, 0))
            dot.create_oval(1, 1, 11, 11, fill=theme.DIM, outline="")
            label = tk.Label(row, text="", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
                             font=self.fonts.ui(11), anchor="w")
            label.pack(side="left", padx=(8, 0))
            self._requirement_rows.append((dot, label))

        spacer = tk.Frame(body, bg=theme.GLASS_BOTTOM)
        spacer.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Hinweis: Der Prüfstand ist eine Heuristik. Er erkennt keine "
                 "Breach-Daten, keine Wiederverwendung und keine Phishing-Angriffe.",
            bg=theme.GLASS_BOTTOM, fg=theme.DIM, font=self.fonts.ui(9),
            wraplength=350, justify="left", anchor="w",
        ).pack(fill="x")

        # -- report column --------------------------------------------------
        right = tk.Frame(self.audit_view, bg=theme.BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        report_panel = GlassPanel(right, pad=20)
        report_panel.pack(fill="both", expand=True)
        report = report_panel.body

        top = tk.Frame(report, bg=theme.GLASS_BOTTOM)
        top.pack(fill="x")
        tk.Label(top, text="BEWERTUNG", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
                 font=self.fonts.ui(9, "bold")).pack(side="left")
        self._audit_rating_pill = tk.Frame(top, bg=theme.GLASS_BOTTOM)
        self._audit_rating_pill.pack(side="right")

        rating_row = tk.Frame(report, bg=theme.GLASS_BOTTOM)
        rating_row.pack(fill="x", pady=(4, 0))
        self._audit_rating = tk.Label(rating_row, text="—", bg=theme.GLASS_BOTTOM,
                                      fg=theme.DIM, font=self.fonts.display(28),
                                      anchor="w")
        self._audit_rating.pack(side="left")
        self._audit_bits = tk.Label(rating_row, text="", bg=theme.GLASS_BOTTOM,
                                    fg=theme.MUTED, font=self.fonts.mono(13),
                                    anchor="e")
        self._audit_bits.pack(side="right", pady=(12, 0))

        self._audit_meter = Meter(report, bg=theme.GLASS_BOTTOM, height=6)
        self._audit_meter.pack(fill="x", pady=(8, 14))

        stats = tk.Frame(report, bg=theme.GLASS_BOTTOM)
        stats.pack(fill="x")
        self._audit_stats: dict[str, tk.Label] = {}
        for index, (key, label) in enumerate(
            (("length", "LÄNGE"), ("pool", "ZEICHENVORRAT"), ("classes", "KLASSEN"))
        ):
            cell = tk.Frame(stats, bg=theme.GLASS_BOTTOM)
            cell.grid(row=0, column=index, sticky="w", padx=(0, 34))
            value = tk.Label(cell, text="—", bg=theme.GLASS_BOTTOM,
                             fg=theme.TEXT, font=self.fonts.mono(18), anchor="w")
            value.pack(anchor="w")
            tk.Label(cell, text=label, bg=theme.GLASS_BOTTOM, fg=theme.DIM,
                     font=self.fonts.ui(9, "bold"), anchor="w").pack(anchor="w")
            self._audit_stats[key] = value

        widgets.divider(report, pady=14)

        tk.Label(report, text="BEFUNDE", bg=theme.GLASS_BOTTOM, fg=theme.MUTED,
                 font=self.fonts.ui(9, "bold"), anchor="w").pack(fill="x")
        self._findings_host = tk.Frame(report, bg=theme.GLASS_BOTTOM)
        self._findings_host.pack(fill="x", pady=(8, 0))

        widgets.divider(report, pady=14)

        attack_head = tk.Frame(report, bg=theme.GLASS_BOTTOM)
        attack_head.pack(fill="x")
        tk.Label(attack_head, text="ANGRIFFSMODELL", bg=theme.GLASS_BOTTOM,
                 fg=theme.MUTED, font=self.fonts.ui(9, "bold")).pack(side="left")
        tk.Label(attack_head, text="MITTLERE TREFFERZEIT", bg=theme.GLASS_BOTTOM,
                 fg=theme.DIM, font=self.fonts.ui(9, "bold")).pack(side="right")
        self._audit_attack_table = AttackTable(report, self.fonts, theme.GLASS_BOTTOM)
        self._audit_attack_table.pack(fill="x", pady=(8, 2))
        tk.Label(
            report,
            text="Schätzung für den eingegebenen Wert, nicht für ein generiertes Passwort.",
            bg=theme.GLASS_BOTTOM, fg=theme.DIM, font=self.fonts.ui(9), anchor="w",
        ).pack(fill="x", pady=(4, 0))

    # ------------------------------------------------------------------
    # Navigation and hotkeys
    # ------------------------------------------------------------------

    def _show_view(self, name: str) -> None:
        if name == self._view and getattr(self, "_view_packed", False):
            return
        self._view = name
        for view in (self.generator_view, self.audit_view):
            view.pack_forget()
        if name == "generator":
            self.generator_view.pack(fill="both", expand=True)
        else:
            self.audit_view.pack(fill="both", expand=True)
            self._audit_entry.focus()
            self._refresh_audit()
        self._view_packed = True
        for key, button in self._tab_buttons.items():
            button.set_active(key == name)

    def _bind_keys(self) -> None:
        self.bind_all("<Control-g>", self._hotkey_generate)
        self.bind_all("<Control-G>", self._hotkey_generate)
        self.bind_all("<Control-h>", self._hotkey_mask)
        self.bind_all("<Control-H>", self._hotkey_mask)
        self.bind_all("<Control-c>", self._hotkey_copy)
        self.bind_all("<Control-C>", self._hotkey_copy)
        self.bind_all("<Control-Shift-C>", self._hotkey_copy_all)
        self.bind_all("<Control-Shift-c>", self._hotkey_copy_all)
        self.bind_all("<F1>", lambda _e: self.show_method())

    def _hotkey_generate(self, _event: tk.Event) -> str:
        self._show_view("generator")
        self.generate()
        return "break"

    def _hotkey_mask(self, _event: tk.Event) -> str:
        self._mask_toggle.set_value(not self._mask_toggle.value, notify=True)
        return "break"

    def _hotkey_copy(self, _event: tk.Event) -> str | None:
        if isinstance(self.focus_get(), (tk.Entry, tk.Text)):
            return None
        self._copy_selected()
        return "break"

    def _hotkey_copy_all(self, _event: tk.Event) -> str:
        self.copy_all()
        return "break"

    # ------------------------------------------------------------------
    # Generator state
    # ------------------------------------------------------------------

    def _policy_from_ui(self) -> core.Policy:
        return core.Policy(
            length=self._length,
            lowercase=self._toggles["lower"].value,
            uppercase=self._toggles["upper"].value,
            digits=self._toggles["digits"].value,
            symbols=self._toggles["symbols"].value,
            exclude_ambiguous=self._ambiguous_toggle.value,
            require_each_class=True,
        )

    def _refresh_policy(self) -> None:
        try:
            policy = self._policy_from_ui()
            policy.validate()
        except core.PolicyError as error:
            self._summary_label.configure(text=str(error), fg=theme.DANGER)
            self._alphabet_label.configure(text="UNGÜLTIG", fg=theme.DANGER)
            return
        self.policy = policy
        sizes = dict(policy.class_sizes())
        for key, label in (("lower", "Kleinbuchstaben"), ("upper", "Großbuchstaben"),
                           ("digits", "Ziffern"), ("symbols", "Sonderzeichen")):
            self._toggles[key].set_subtitle(f"{sizes.get(label, 0)} Zeichen")
        self._alphabet_label.configure(text=f"{len(policy.alphabet())} ZEICHEN",
                                       fg=theme.DIM)
        bits = core.entropy_bits(policy)
        self._summary_label.configure(
            text=f"{policy.length} Zeichen · {len(policy.alphabet())} Vorrat · "
                 f"{core.format_bits(bits)}",
            fg=theme.ACCENT,
        )

    def _on_policy_toggle(self, _value: bool) -> None:
        self._refresh_policy()

    def _on_length_change(self, value: int) -> None:
        self._length = value
        self._length_label.configure(text=str(value))
        self._refresh_policy()

    def _set_length(self, value: int) -> None:
        self._length_slider.set_value(value)
        self._on_length_change(value)

    def _on_count_change(self, value: str) -> None:
        self._count = int(value)
        if self._passwords:
            self.generate()

    def _on_mask_toggle(self, value: bool) -> None:
        self._masked = value
        if self._passwords:
            self._render_cards()

    def _on_clipboard_change(self, value: str) -> None:
        self._clip_seconds = int(value)
        if self._clip_seconds == 0:
            self._feedback("Automatisches Leeren der Zwischenablage ist aus", "warn")
        else:
            self._feedback(f"Zwischenablage leert nach {self._clip_seconds} Sekunden",
                           "muted")

    def generate(self) -> None:
        try:
            policy = self._policy_from_ui()
            policy.validate()
            self.policy = policy
            passwords = core.generate_many(policy, self._count)
        except core.PolicyError as error:
            self._feedback(str(error), "danger")
            return

        self._passwords = passwords
        self._selected = 0
        self._render_cards()
        bits = core.entropy_bits(policy)
        self._feedback(
            f"{len(passwords)} Schlüssel erzeugt · {core.format_bits(bits)}",
            "accent",
        )

    def _render_cards(self) -> None:
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        if not self._passwords:
            self._cards_host.pack_forget()
            self._empty_state.pack(pady=64)
            self._results_subtitle.configure(text="0 SCHLÜSSEL")
            self.attack_table.set_bits(0.0, known=False)
            return

        self._empty_state.pack_forget()
        self._cards_host.pack(fill="x")
        bits = core.entropy_bits(self.policy)
        rating = core.rating_for(bits)
        for index, password in enumerate(self._passwords):
            card = PasswordCard(
                self._cards_host, index, password, bits, rating, self._masked,
                self._copy_index, self._select_card, self.fonts, theme.BG,
            )
            card.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            card.set_selected(index == self._selected)
            self._cards.append(card)
        self._results_subtitle.configure(
            text=f"{len(self._passwords)} " +
                 ("SCHLÜSSEL" if len(self._passwords) > 1 else "SCHLÜSSEL")
        )
        self.attack_table.set_bits(bits)
        self._results_scroll.scroll_to_top()

    def _select_card(self, index: int) -> None:
        self._selected = index
        for card in self._cards:
            card.set_selected(card.index == index)
        self.attack_table.set_bits(core.entropy_bits(self.policy))

    def _copy_index(self, index: int) -> None:
        if 0 <= index < len(self._passwords):
            self._selected = index
            self._select_card(index)
            self._to_clipboard(self._passwords[index], "Passwort kopiert")

    def _copy_selected(self) -> None:
        if not self._passwords:
            self._feedback("Keine Ausgabe vorhanden", "warn")
            return
        self._copy_index(min(self._selected, len(self._passwords) - 1))

    def copy_all(self) -> None:
        if not self._passwords:
            self._feedback("Keine Ausgabe vorhanden", "warn")
            return
        self._to_clipboard("\n".join(self._passwords), "Alle Passwörter kopiert")

    def _copy_audit(self) -> None:
        value = self._audit_entry.get()
        if not value:
            self._feedback("Prüfstand ist leer", "warn")
            return
        self._to_clipboard(value, "Passwort kopiert")

    def _to_clipboard(self, value: str, message: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(value)
            self.update_idletasks()
        except tk.TclError:
            self._feedback("Zwischenablage nicht verfügbar", "danger")
            return
        self._clip_text = value
        if self._clip_job:
            self.after_cancel(self._clip_job)
            self._clip_job = None
        if self._clip_seconds:
            self._clip_job = self.after(self._clip_seconds * 1000,
                                        self._clear_clipboard)
            self._feedback(f"{message} · Löschung in {self._clip_seconds} s", "accent")
        else:
            self._feedback(message, "accent")

    def _clear_clipboard(self) -> None:
        self._clip_job = None
        if self._clip_text is None:
            return
        try:
            if self.clipboard_get() == self._clip_text:
                self.clipboard_clear()
                self.update_idletasks()
                self._feedback("Zwischenablage gelöscht", "muted")
        except tk.TclError:
            pass
        self._clip_text = None

    # ------------------------------------------------------------------
    # Audit state
    # ------------------------------------------------------------------

    def _on_audit_show(self, value: bool) -> None:
        self._audit_entry.entry.configure(show="" if value else "•")

    def _on_audit_change(self, _value: str) -> None:
        if self._audit_job:
            self.after_cancel(self._audit_job)
        self._audit_job = self.after(140, self._refresh_audit)

    def _refresh_audit(self) -> None:
        self._audit_job = None
        password = self._audit_entry.get()
        if not password:
            self._reset_audit()
            return

        report = core.audit_password(password)
        self._audit_rating.configure(text=report.rating.label,
                                     fg=theme.tone(report.rating.tone))
        self._audit_bits.configure(text=f"≈ {core.format_bits(report.effective_bits)}")
        self._audit_meter.set(min(1.0, report.effective_bits / 160.0),
                              report.rating.tone)
        self._audit_stats["length"].configure(text=str(report.length))
        self._audit_stats["pool"].configure(text=str(report.pool))
        self._audit_stats["classes"].configure(text=str(core.class_count(password)))

        for child in self._audit_rating_pill.winfo_children():
            child.destroy()
        Pill(self._audit_rating_pill, report.rating.label, report.rating.tone,
             bg=theme.GLASS_BOTTOM, font=self.fonts.ui(9, "bold")).pack()

        for child in self._findings_host.winfo_children():
            child.destroy()
        for finding in report.findings:
            row = tk.Frame(self._findings_host, bg=theme.GLASS_BOTTOM)
            row.pack(fill="x", pady=2)
            tone = theme.tone(finding.severity)
            marker = tk.Canvas(row, width=10, height=10, bg=theme.GLASS_BOTTOM,
                               highlightthickness=0)
            marker.pack(side="left", pady=(3, 0))
            marker.create_oval(1, 1, 9, 9, fill=tone, outline="")
            tk.Label(row, text=finding.text, bg=theme.GLASS_BOTTOM,
                     fg=theme.MUTED, font=self.fonts.ui(11), anchor="w",
                     wraplength=560, justify="left").pack(side="left", padx=(8, 0))

        for (dot, label), requirement in zip(self._requirement_rows,
                                             report.requirements):
            dot.delete("all")
            color = theme.OK if requirement.passed else theme.DANGER
            dot.create_oval(1, 1, 11, 11, fill=color, outline="")
            label.configure(text=requirement.label,
                            fg=theme.MUTED if requirement.passed else theme.DANGER)

        self._audit_attack_table.set_bits(report.effective_bits)

    def _reset_audit(self) -> None:
        self._audit_rating.configure(text="—", fg=theme.DIM)
        self._audit_bits.configure(text="")
        self._audit_meter.set(0.0, "muted")
        for label in self._audit_stats.values():
            label.configure(text="—")
        for child in self._audit_rating_pill.winfo_children():
            child.destroy()
        for child in self._findings_host.winfo_children():
            child.destroy()
        for dot, label in self._requirement_rows:
            dot.delete("all")
            dot.create_oval(1, 1, 11, 11, fill=theme.DIM, outline="")
            label.configure(text="", fg=theme.DIM)
        self._audit_attack_table.set_bits(0.0, known=False)

    # ------------------------------------------------------------------
    # Method dialog, errors, shutdown
    # ------------------------------------------------------------------

    def show_method(self) -> None:
        if self._info_window and self._info_window.winfo_exists():
            self._info_window.lift()
            self._info_window.focus_force()
            return

        window = tk.Toplevel(self)
        self._info_window = window
        window.title("Methodik · PWGen")
        window.configure(bg=theme.BG)
        window.transient(self)
        window.resizable(False, False)
        width, height = 760, 640
        x = self.winfo_rootx() + max(0, (self.winfo_width() - width) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.grab_set()

        shell = tk.Frame(window, bg=theme.BG, padx=24, pady=20)
        shell.pack(fill="both", expand=True)
        header = tk.Frame(shell, bg=theme.BG)
        header.pack(fill="x")
        tk.Label(header, text="METHODIK & HINWEISE", bg=theme.BG, fg=theme.TEXT,
                 font=self.fonts.ui(15, "bold")).pack(side="left")
        tk.Label(header, text=f"PWGEN {core.APP_VERSION}", bg=theme.BG,
                 fg=theme.ACCENT, font=self.fonts.mono(10)).pack(side="right",
                                                                 pady=(6, 0))

        text_frame = tk.Frame(shell, bg=theme.SURFACE_SOLID,
                              highlightbackground=theme.BORDER,
                              highlightthickness=1)
        text_frame.pack(fill="both", expand=True, pady=(14, 14))
        text = tk.Text(text_frame, bg=theme.SURFACE_SOLID, fg=theme.MUTED,
                       bd=0, relief="flat", wrap="word", padx=18, pady=16,
                       insertwidth=0, cursor="arrow", highlightthickness=0,
                       font=self.fonts.ui(11), spacing1=2, spacing3=2)
        scrollbar = tk.Scrollbar(text_frame, command=text.yview, width=8,
                                 bg=theme.SURFACE_SOLID, troughcolor=theme.BG,
                                 activebackground=theme.BORDER_STRONG, bd=0,
                                 relief="flat", highlightthickness=0)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.tag_configure("h", foreground=theme.ACCENT,
                           font=self.fonts.mono(10, "bold"), spacing1=16,
                           spacing3=4)
        text.tag_configure("p", foreground=theme.MUTED, font=self.fonts.ui(11),
                           spacing3=6, lmargin1=0, lmargin2=0)
        text.configure(state="normal")
        for kind, content in METHOD_TEXT:
            text.insert("end", content + "\n", kind)
        text.configure(state="disabled")

        footer = tk.Frame(shell, bg=theme.BG)
        footer.pack(fill="x")
        tk.Label(footer, text="© Dogukan S. · DGKN@Labs · MIT-Lizenz",
                 bg=theme.BG, fg=theme.DIM, font=self.fonts.ui(9)).pack(side="left")
        Button(footer, "SCHLIESSEN", window.destroy, variant="ghost",
               height=34, font=self.fonts.ui(10, "bold"),
               bg=theme.BG).pack(side="right")

        window.bind("<Escape>", lambda _e: window.destroy())
        window.protocol("WM_DELETE_WINDOW", window.destroy)

    def _on_unexpected_error(self, exc_type, exc_value, tb) -> None:
        traceback.print_exception(exc_type, exc_value, tb)
        try:
            messagebox.showerror(
                "Unerwarteter Fehler",
                f"Die Anwendung hat einen Fehler abgefangen:\n\n{exc_value}",
                parent=self,
            )
        except Exception:
            pass

    def _on_close(self) -> None:
        if self._feedback_job:
            self.after_cancel(self._feedback_job)
        if self._clip_job:
            self.after_cancel(self._clip_job)
        if self._clip_text:
            try:
                if self.clipboard_get() == self._clip_text:
                    self.clipboard_clear()
            except tk.TclError:
                pass
        self.destroy()


def _emit(text: str) -> None:
    """Print when a console exists; windowed builds have sys.stdout = None."""

    stream = sys.stdout
    if stream is None:
        return
    try:
        print(text, file=stream)
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--version" in args:
        _emit(f"{core.APP_NAME} {core.APP_VERSION} · {core.VENDOR}")
        return 0
    if "--help" in args or "-h" in args:
        _emit(USAGE)
        return 0
    if "--self-test" in args:
        ok, lines = core.self_test()
        for line in lines:
            _emit(line)
        _emit("ERGEBNIS: " + ("OK" if ok else "FEHLER"))
        return 0 if ok else 1
    if "--smoke-ui" in args:
        app = App()
        app.update_idletasks()
        app.update()
        app.destroy()
        _emit("UI-SMOKE OK")
        return 0
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
