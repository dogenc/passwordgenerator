"""Canvas-based glass widget kit.

Tk has no real transparency or backdrop blur, so the "glass" look is built
from layered rounded surfaces, a soft gradient rim, a 1px specular highlight
and restrained accent colours.  Everything is drawn manually to keep the app
dependency-free and visually consistent on Windows, Linux and macOS.
"""

from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Sequence

from . import theme


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------


def _arc_points(cx: float, cy: float, radius: float, start: float, end: float,
                steps: int = 6) -> list[float]:
    points: list[float] = []
    for index in range(steps + 1):
        angle = math.radians(start + (end - start) * index / steps)
        points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def rounded_points(x0: float, y0: float, x1: float, y1: float,
                   radius: float, steps: int = 6) -> list[float]:
    radius = max(0.0, min(radius, (x1 - x0) / 2, (y1 - y0) / 2))
    points: list[float] = []
    points += _arc_points(x1 - radius, y0 + radius, radius, 270, 360, steps)
    points += _arc_points(x1 - radius, y1 - radius, radius, 0, 90, steps)
    points += _arc_points(x0 + radius, y1 - radius, radius, 90, 180, steps)
    points += _arc_points(x0 + radius, y0 + radius, radius, 180, 270, steps)
    return points


def rounded(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float,
            radius: float, **kwargs: object) -> int:
    return canvas.create_polygon(
        rounded_points(x0, y0, x1, y1, radius), smooth=False, **kwargs
    )


def draw_glyph(canvas: tk.Canvas, name: str, cx: float, cy: float, size: float,
               color: str, width: float = 1.6, tags: str = "") -> None:
    """Minimal vector icon set, drawn in the current widget's colours."""

    s = size / 2.0
    common = {"outline": color, "width": width, "tags": tags}
    if name == "copy":
        canvas.create_rectangle(cx - s * 0.55, cy - s * 0.65, cx + s * 0.55,
                                cy + s * 0.45, **common)
        canvas.create_line(cx - s * 0.8, cy - s * 0.3, cx - s * 0.8,
                           cy + s * 0.8, cx + s * 0.35, cy + s * 0.8,
                           fill=color, width=width, capstyle="round", tags=tags)
    elif name == "eye":
        canvas.create_oval(cx - s, cy - s * 0.62, cx + s, cy + s * 0.62, **common)
        canvas.create_oval(cx - s * 0.28, cy - s * 0.28, cx + s * 0.28,
                           cy + s * 0.28, outline=color, width=width, tags=tags)
    elif name == "eye_off":
        canvas.create_oval(cx - s, cy - s * 0.62, cx + s, cy + s * 0.62, **common)
        canvas.create_line(cx - s * 0.9, cy + s * 0.9, cx + s * 0.9,
                           cy - s * 0.9, fill=color, width=width, tags=tags)
    elif name == "lock":
        canvas.create_arc(cx - s * 0.55, cy - s, cx + s * 0.55, cy + s * 0.1,
                          start=0, extent=180, style="arc", outline=color,
                          width=width, tags=tags)
        rounded(canvas, cx - s * 0.75, cy - s * 0.05, cx + s * 0.75,
                cy + s * 0.9, s * 0.2, outline=color, fill="", width=width, tags=tags)
        canvas.create_line(cx, cy + s * 0.25, cx, cy + s * 0.55, fill=color,
                           width=width, tags=tags)
    elif name == "shield":
        points = [
            cx, cy - s,
            cx + s * 0.82, cy - s * 0.55,
            cx + s * 0.72, cy + s * 0.35,
            cx, cy + s,
            cx - s * 0.72, cy + s * 0.35,
            cx - s * 0.82, cy - s * 0.55,
        ]
        canvas.create_polygon(points, outline=color, fill="", width=width,
                              joinstyle="round", tags=tags)
        canvas.create_line(cx - s * 0.3, cy, cx - s * 0.05, cy + s * 0.3,
                           cx + s * 0.36, cy - s * 0.3, fill=color, width=width,
                           capstyle="round", joinstyle="round", tags=tags)
    elif name == "check":
        canvas.create_line(cx - s * 0.7, cy, cx - s * 0.15, cy + s * 0.55,
                           cx + s * 0.75, cy - s * 0.55, fill=color,
                           width=width + 0.4, capstyle="round",
                           joinstyle="round", tags=tags)
    elif name == "close":
        canvas.create_line(cx - s * 0.6, cy - s * 0.6, cx + s * 0.6, cy + s * 0.6,
                           fill=color, width=width, capstyle="round", tags=tags)
        canvas.create_line(cx + s * 0.6, cy - s * 0.6, cx - s * 0.6, cy + s * 0.6,
                           fill=color, width=width, capstyle="round", tags=tags)
    elif name == "alert":
        canvas.create_polygon(cx, cy - s, cx + s, cy + s * 0.85, cx - s,
                              cy + s * 0.85, outline=color, fill="", width=width,
                              joinstyle="round", tags=tags)
        canvas.create_line(cx, cy - s * 0.3, cx, cy + s * 0.25, fill=color,
                           width=width, tags=tags)
        canvas.create_line(cx, cy + s * 0.55, cx, cy + s * 0.62, fill=color,
                           width=width + 0.6, tags=tags)
    elif name == "refresh":
        canvas.create_arc(cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8,
                          start=30, extent=280, style="arc", outline=color,
                          width=width, tags=tags)
        canvas.create_polygon(cx + s * 0.55, cy - s * 0.9, cx + s * 0.9,
                              cy - s * 0.45, cx + s * 0.25, cy - s * 0.42,
                              fill=color, outline="", tags=tags)
    elif name == "key":
        canvas.create_oval(cx - s * 0.85, cy - s * 0.85, cx - s * 0.1,
                           cy - s * 0.1, outline=color, width=width, tags=tags)
        canvas.create_line(cx - s * 0.35, cy - s * 0.35, cx + s * 0.85,
                           cy + s * 0.85, fill=color, width=width,
                           capstyle="round", tags=tags)
        canvas.create_line(cx + s * 0.35, cy + s * 0.35, cx + s * 0.6,
                           cy + s * 0.1, fill=color, width=width, tags=tags)
        canvas.create_line(cx + s * 0.6, cy + s * 0.6, cx + s * 0.85,
                           cy + s * 0.35, fill=color, width=width, tags=tags)
    elif name == "clock":
        canvas.create_oval(cx - s * 0.85, cy - s * 0.85, cx + s * 0.85,
                           cy + s * 0.85, outline=color, width=width, tags=tags)
        canvas.create_line(cx, cy - s * 0.45, cx, cy, cx + s * 0.4, cy + s * 0.25,
                           fill=color, width=width, capstyle="round",
                           joinstyle="round", tags=tags)


def measure(font: tuple, text: str) -> int:
    return tkfont.Font(font=font).measure(text)


# --------------------------------------------------------------------------
# Surfaces
# --------------------------------------------------------------------------


class GlassPanel(tk.Frame):
    """Rounded surface with a soft vertical gradient rim and hairline border."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        pad: int = theme.PANEL_PAD,
        radius: int = theme.PANEL_RADIUS,
        top: str = theme.GLASS_TOP,
        bottom: str = theme.GLASS_BOTTOM,
        border: str = theme.BORDER,
        bg: str | None = None,
        **kwargs: object,
    ) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, bg=base, **kwargs)
        self._base_bg = base
        self._top = top
        self._bottom = bottom
        self._border = border
        self._radius = radius
        self._pad = pad
        self._size: tuple[int, int] | None = None

        self.canvas = tk.Canvas(self, bg=base, highlightthickness=0, bd=0,
                                takefocus=0)
        self.canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=bottom)
        self._body_window = self.canvas.create_window(
            pad, pad, anchor="nw", window=self.body, width=1, height=1
        )
        self.canvas.bind("<Configure>", self._on_configure)

    # -- state ------------------------------------------------------------
    def set_border(self, color: str) -> None:
        if color == self._border:
            return
        self._border = color
        self._redraw()

    def set_surface(self, top: str, bottom: str) -> None:
        self._top = top
        self._bottom = bottom
        self.body.configure(bg=bottom)
        self._redraw()

    # -- painting ---------------------------------------------------------
    def _on_configure(self, event: tk.Event) -> None:
        size = (max(int(event.width), 1), max(int(event.height), 1))
        if size == self._size:
            return
        self._size = size
        self.canvas.itemconfigure(
            self._body_window,
            width=max(1, size[0] - 2 * self._pad),
            height=max(1, size[1] - 2 * self._pad),
        )
        self._redraw()

    def _redraw(self) -> None:
        if not self._size:
            return
        width, height = self._size
        if width < 4 or height < 4:
            return
        canvas = self.canvas
        canvas.delete("deco")

        steps = 36
        for index in range(steps):
            y0 = height * index / steps
            y1 = height * (index + 1) / steps
            color = theme.mix(self._top, self._bottom, index / (steps - 1))
            canvas.create_rectangle(0, y0, width, y1 + 1, fill=color,
                                    outline="", tags="deco")

        radius = min(self._radius, width / 2, height / 2)
        self._mask_corners(radius, width, height)

        rounded(canvas, 0.5, 0.5, width - 0.5, height - 0.5, radius,
                fill="", outline=self._border, width=1, tags="deco")
        canvas.create_line(radius, 1, width - radius, 1,
                           fill=theme.mix(self._top, theme.WHITE, 0.10),
                           tags="deco")
        canvas.tag_lower("deco")

    def _mask_corners(self, radius: float, width: float, height: float) -> None:
        canvas = self.canvas
        steps = 8
        polygons = [
            [(0, 0), (radius, 0)]
            + _arc_points(radius, radius, radius, 270, 180, steps),
            [(width - radius, 0), (width, 0), (width, radius)]
            + _arc_points(width - radius, radius, radius, 0, -90, steps),
            [(width, height - radius), (width, height), (width - radius, height)]
            + _arc_points(width - radius, height - radius, radius, 90, 0, steps),
            [(radius, height), (0, height), (0, height - radius)]
            + _arc_points(radius, height - radius, radius, 180, 90, steps),
        ]
        for points in polygons:
            canvas.create_polygon(points, fill=self._base_bg, outline="",
                                  tags="deco")


class ScrollArea(tk.Frame):
    """Vertical scroll container with a slim, dark scrollbar."""

    def __init__(self, master: tk.Misc, *, bg: str | None = None,
                 bar_width: int = 6) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, bg=base)
        self._base_bg = base
        self._bar_width = bar_width
        self._wheel_bound = False

        self.canvas = tk.Canvas(self, bg=base, highlightthickness=0, bd=0,
                                yscrollincrement=18)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar = tk.Canvas(self, bg=base, width=bar_width,
                             highlightthickness=0, bd=0)
        self.bar.pack(side="right", fill="y", padx=(10, 0))

        self.inner = tk.Frame(self.canvas, bg=base)
        self._window = self.canvas.create_window((0, 0), anchor="nw",
                                                 window=self.inner)
        self.inner.bind("<Configure>", self._sync)
        self.canvas.bind("<Configure>", self._sync)
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.bar.bind("<Button-1>", self._on_bar_click)
        self.bar.bind("<B1-Motion>", self._on_bar_drag)
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)

    def _on_scroll(self, first: str, last: str) -> None:
        self._draw_bar(float(first), float(last))

    def _sync(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfigure(self._window,
                                  width=max(1, self.canvas.winfo_width()))
        self._draw_bar(*self.canvas.yview())

    def _draw_bar(self, first: float, last: float) -> None:
        bar = self.bar
        bar.delete("all")
        height = bar.winfo_height()
        if height < 10:
            return
        inset = 2
        bar.create_line(inset + 1, 4, inset + 1, height - 4,
                        fill=theme.HAIRLINE, width=1)
        if first <= 0.0 and last >= 1.0:
            return
        top = max(4, int(first * height) + 2)
        bottom = min(height - 4, int(last * height) - 2)
        if bottom - top < 18:
            bottom = min(height - 4, top + 18)
        rounded(bar, inset, top, inset + 3, bottom, 2,
                fill=theme.BORDER_STRONG, outline="")

    def _bind_wheel(self, _event: tk.Event) -> None:
        if self._wheel_bound:
            return
        self._wheel_bound = True
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.bind_all("<Button-4>", self._on_wheel_linux, add="+")
        self.bind_all("<Button-5>", self._on_wheel_linux, add="+")

    def _unbind_wheel(self, _event: tk.Event | None = None) -> None:
        if not self._wheel_bound:
            return
        self._wheel_bound = False
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_wheel(self, event: tk.Event) -> None:
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta * 2, "units")
        self._draw_bar(*self.canvas.yview())

    def _on_wheel_linux(self, event: tk.Event) -> None:
        delta = -2 if event.num == 4 else 2
        self.canvas.yview_scroll(delta, "units")
        self._draw_bar(*self.canvas.yview())

    def _on_bar_click(self, event: tk.Event) -> None:
        self._scroll_to(event.y)

    def _on_bar_drag(self, event: tk.Event) -> None:
        self._scroll_to(event.y)

    def _scroll_to(self, y: int) -> None:
        height = max(1, self.bar.winfo_height())
        first, last = self.canvas.yview()
        span = max(0.05, last - first)
        fraction = max(0.0, min(1.0 - span, y / height - span / 2))
        self.canvas.yview_moveto(fraction)
        self._draw_bar(*self.canvas.yview())

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0.0)
        self._draw_bar(*self.canvas.yview())


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------


class Button(tk.Canvas):
    _VARIANTS = {
        "primary": (theme.ACCENT, theme.INVERSE, theme.ACCENT),
        "ghost": (None, theme.TEXT, theme.BORDER_STRONG),
        "subtle": (None, theme.MUTED, theme.BORDER),
        "danger": (None, theme.DANGER, theme.mix(theme.DANGER, theme.BG, 0.55)),
    }

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        *,
        variant: str = "primary",
        height: int = 44,
        width: int | None = None,
        bg: str | None = None,
        font: tuple | None = None,
        icon: str | None = None,
        radius: int = 12,
    ) -> None:
        base = bg or master.cget("bg")
        self._font = font or (theme.load_fonts(master)._ui_family, -14, "bold")
        self._icon = icon
        text_width = measure(self._font, text)
        if width is None:
            width = text_width + (44 if icon else 34)
        super().__init__(master, width=width, height=height, bg=base,
                         highlightthickness=0, bd=0, takefocus=1,
                         cursor="hand2")
        self._text = text
        self._command = command
        self._variant = variant
        self._radius = radius
        self._base_bg = base
        self._state = "normal"
        self._focus = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", lambda _e: self.invoke())
        self.bind("<space>", lambda _e: self.invoke())
        self._redraw()

    def invoke(self) -> None:
        if self._command and self._state != "disabled":
            self._command()

    def set_text(self, text: str) -> None:
        self._text = text
        self._redraw()

    def _on_enter(self, _event: tk.Event) -> None:
        self._state = "hover"
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._state = "normal"
        self._redraw()

    def _on_press(self, _event: tk.Event) -> None:
        self.focus_set()
        self._state = "press"
        self._redraw()

    def _on_release(self, event: tk.Event) -> None:
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        self._state = "hover" if inside else "normal"
        self._redraw()
        if inside:
            self.invoke()

    def _on_focus_in(self, _event: tk.Event) -> None:
        self._focus = True
        self._redraw()

    def _on_focus_out(self, _event: tk.Event) -> None:
        self._focus = False
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), int(self["width"]))
        height = max(self.winfo_height(), int(self["height"]))
        fill, text_color, border = self._VARIANTS.get(self._variant, self._VARIANTS["subtle"])

        if fill is None:
            tint = theme.ACCENT if self._variant == "ghost" else theme.WHITE
            fill = theme.blend(tint, 0.05 if self._variant == "ghost" else 0.03, self._base_bg)
        if self._variant == "primary":
            fill = theme.mix(fill, theme.WHITE, 0.14) if self._state == "hover" else fill
            fill = theme.mix(fill, theme.BG, 0.16) if self._state == "press" else fill
            border = fill
        else:
            fill = theme.blend(text_color, 0.09 if self._state == "hover" else 0.03,
                               self._base_bg)
            border = theme.mix(border, text_color, 0.35) if self._state == "hover" else border

        if self._focus:
            border = theme.mix(border, theme.ACCENT, 0.7)

        rounded(self, 0.5, 0.5, width - 0.5, height - 0.5, self._radius,
                fill=fill, outline=border, width=1)

        content_width = measure(self._font, self._text) + (22 if self._icon else 0)
        start = (width - content_width) / 2
        if self._icon:
            draw_glyph(self, self._icon, start + 6, height / 2, 13, text_color)
            start += 22
        self.create_text(start, height / 2 - 1, text=self._text, anchor="w",
                         fill=text_color, font=self._font)


class IconButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        glyph: str,
        command: Callable[[], None] | None = None,
        *,
        size: int = 34,
        bg: str | None = None,
        tone: str = theme.MUTED,
        tooltip: str = "",
    ) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, width=size, height=size, bg=base,
                         highlightthickness=0, bd=0, takefocus=1,
                         cursor="hand2")
        self._glyph = glyph
        self._command = command
        self._tone = tone
        self._base_bg = base
        self._hover = False
        self._focus = False
        self.tooltip = tooltip
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Return>", lambda _e: self._command and self._command())
        self.bind("<space>", lambda _e: self._command and self._command())
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_focus)
        self._redraw()

    def _on_enter(self, _event: tk.Event) -> None:
        self._hover = True
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover = False
        self._redraw()

    def _on_click(self, _event: tk.Event) -> None:
        self.focus_set()
        if self._command:
            self._command()

    def _on_focus(self, _event: tk.Event) -> None:
        self._focus = not self._focus
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        size = self.winfo_width() if self.winfo_width() > 1 else int(self["width"])
        if self._hover or self._focus:
            rounded(self, 1, 1, size - 1, size - 1, 8,
                    fill=theme.blend(theme.WHITE, 0.06, self._base_bg),
                    outline=theme.BORDER if not self._focus else theme.ACCENT_SOFT,
                    width=1)
        draw_glyph(self, self._glyph, size / 2, size / 2, 14,
                   theme.mix(self._tone, theme.WHITE, 0.35) if self._hover else self._tone)


class Switch(tk.Canvas):
    def __init__(self, master: tk.Misc, value: bool, command: Callable[[bool], None],
                 *, width: int = 40, height: int = 22,
                 bg: str | None = None) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, width=width, height=height, bg=base,
                         highlightthickness=0, bd=0, takefocus=1,
                         cursor="hand2")
        self._value = value
        self._command = command
        self._base_bg = base
        self._width = width
        self._height = height
        self._pos = 1.0 if value else 0.0
        self._animation: str | None = None
        self.bind("<Button-1>", self._on_click)
        self.bind("<Return>", lambda _e: self._on_click(None))
        self.bind("<space>", lambda _e: self._on_click(None))
        self._redraw()

    def _on_click(self, _event: tk.Event | None) -> None:
        self._value = not self._value
        self._command(self._value)
        self._animate()

    def _animate(self) -> None:
        target = 1.0 if self._value else 0.0
        if self._animation:
            self.after_cancel(self._animation)
            self._animation = None

        def step() -> None:
            delta = target - self._pos
            if abs(delta) < 0.02:
                self._pos = target
                self._redraw()
                self._animation = None
                return
            self._pos += delta * 0.35
            self._redraw()
            self._animation = self.after(12, step)

        step()

    def _redraw(self) -> None:
        self.delete("all")
        width, height = self._width, self._height
        track = theme.blend(theme.ACCENT, 0.7 * self._pos + 0.06, self._base_bg)
        rounded(self, 0.5, 0.5, width - 0.5, height - 0.5, height / 2,
                fill=track,
                outline=theme.mix(theme.BORDER, theme.ACCENT, 0.5 * self._pos),
                width=1)
        knob_x = height / 2 + self._pos * (width - height)
        knob_color = theme.ACCENT if self._pos > 0.5 else theme.DIM
        radius = height / 2 - 4.5
        self.create_oval(knob_x - radius, height / 2 - radius,
                         knob_x + radius, height / 2 + radius,
                         fill=theme.mix(knob_color, theme.WHITE, 0.72),
                         outline="")


class ToggleRow(tk.Frame):
    """Label + subtitle on the left, animated switch on the right."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        subtitle: str = "",
        *,
        value: bool = True,
        on_change: Callable[[bool], None] | None = None,
        fonts: theme.Fonts,
        bg: str | None = None,
        title_size: int = 13,
    ) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, bg=base)
        self._fonts = fonts
        self.columnconfigure(0, weight=1)

        self.title_label = tk.Label(self, text=title, bg=base, fg=theme.TEXT,
                                    font=fonts.ui(title_size), anchor="w")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = tk.Label(self, text=subtitle, bg=base, fg=theme.DIM,
                                       font=fonts.ui(10), anchor="w")
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        if not subtitle:
            self.subtitle_label.grid_remove()

        self.switch = Switch(self, value, self._on_switch, bg=base)
        self.switch.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        for widget in (self, self.title_label, self.subtitle_label):
            widget.bind("<Button-1>", lambda _e: self.switch._on_click(None))

    def _on_switch(self, value: bool) -> None:
        if self._callback:
            self._callback(value)

    _callback: Callable[[bool], None] | None = None

    def set_callback(self, callback: Callable[[bool], None]) -> None:
        self._callback = callback

    @property
    def value(self) -> bool:
        return self.switch._value

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.configure(text=text)
        if text:
            self.subtitle_label.grid()
        else:
            self.subtitle_label.grid_remove()

    def set_value(self, value: bool, notify: bool = False) -> None:
        if self.switch._value == value:
            return
        self.switch._value = value
        self.switch._pos = 1.0 if value else 0.0
        self.switch._redraw()
        if notify and self._callback:
            self._callback(value)


class Slider(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        *,
        minimum: int = 8,
        maximum: int = 128,
        value: int = 20,
        on_change: Callable[[int], None] | None = None,
        bg: str | None = None,
        height: int = 34,
        step: int = 1,
    ) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, height=height, bg=base, highlightthickness=0,
                         bd=0, takefocus=1, cursor="hand2")
        self._min = minimum
        self._max = maximum
        self._value = max(minimum, min(maximum, value))
        self._on_change = on_change
        self._base_bg = base
        self._height = height
        self._step = step
        self._dragging = False
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Left>", lambda _e: self._nudge(-step))
        self.bind("<Right>", lambda _e: self._nudge(step))
        self.bind("<Prior>", lambda _e: self._nudge(step * 8))
        self.bind("<Next>", lambda _e: self._nudge(-step * 8))
        self.bind("<Home>", lambda _e: self._set(self._min, True))
        self.bind("<End>", lambda _e: self._set(self._max, True))
        self._redraw()

    def _padding(self) -> int:
        return 12

    def _value_to_x(self, value: float) -> float:
        width = max(self.winfo_width(), 60)
        span = width - 2 * self._padding()
        ratio = (value - self._min) / max(1, self._max - self._min)
        return self._padding() + ratio * span

    def _x_to_value(self, x: float) -> int:
        width = max(self.winfo_width(), 60)
        span = max(1, width - 2 * self._padding())
        ratio = (x - self._padding()) / span
        ratio = max(0.0, min(1.0, ratio))
        raw = self._min + ratio * (self._max - self._min)
        return int(round(raw / self._step) * self._step)

    def _on_press(self, event: tk.Event) -> None:
        self.focus_set()
        self._dragging = True
        self._set(self._x_to_value(event.x), True)

    def _on_drag(self, event: tk.Event) -> None:
        if self._dragging:
            self._set(self._x_to_value(event.x), True)

    def _on_release(self, _event: tk.Event) -> None:
        self._dragging = False

    def _nudge(self, delta: int) -> None:
        self._set(self._value + delta, True)

    def _set(self, value: int, notify: bool = False) -> None:
        value = max(self._min, min(self._max, value))
        if value == self._value:
            return
        self._value = value
        self._redraw()
        if notify and self._on_change:
            self._on_change(value)

    def set_value(self, value: int, notify: bool = False) -> None:
        self._set(value, notify)

    @property
    def value(self) -> int:
        return self._value

    def _redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 60)
        center = self._height / 2
        x0, x1 = self._padding(), width - self._padding()
        track_top, track_bottom = center - 3, center + 3
        rounded(self, x0, track_top, x1, track_bottom, 3,
                fill=theme.mix(theme.BORDER, theme.BG, 0.35), outline="")
        knob_x = self._value_to_x(self._value)
        if knob_x > x0 + 1:
            rounded(self, x0, track_top, knob_x, track_bottom, 3,
                    fill=theme.ACCENT_SOFT, outline="")
        self.create_oval(knob_x - 10, center - 10, knob_x + 10, center + 10,
                         fill=theme.blend(theme.ACCENT, 0.10, self._base_bg),
                         outline="")
        self.create_oval(knob_x - 7, center - 7, knob_x + 7, center + 7,
                         fill=theme.mix(theme.ACCENT, theme.WHITE, 0.55),
                         outline=theme.ACCENT, width=1)


class Segmented(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        options: Sequence[tuple[str, str]],
        value: str,
        on_change: Callable[[str], None] | None = None,
        *,
        bg: str | None = None,
        font: tuple | None = None,
        height: int = 30,
        width: int | None = None,
    ) -> None:
        base = bg or master.cget("bg")
        self._font = font or (theme.load_fonts(master)._ui_family, -11, "bold")
        self._items = list(options)
        if width is None:
            width = max(measure(self._font, label) for _, label in self._items) * len(self._items) + 28 * len(self._items)
        super().__init__(master, width=width, height=height, bg=base,
                         highlightthickness=0, bd=0, takefocus=1,
                         cursor="hand2")
        self._value = value
        self._on_change = on_change
        self._base_bg = base
        self._height = height
        self._hover_index = -1
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Left>", lambda _e: self._move(-1))
        self.bind("<Right>", lambda _e: self._move(1))
        self._redraw()

    def _segment_width(self) -> float:
        width = max(self.winfo_width(), 20)
        return width / len(self._items)

    def _on_click(self, event: tk.Event) -> None:
        self.focus_set()
        index = min(len(self._items) - 1, int(event.x / self._segment_width()))
        value = self._items[index][0]
        if value != self._value:
            self._value = value
            self._redraw()
            if self._on_change:
                self._on_change(value)

    def _on_motion(self, event: tk.Event) -> None:
        index = min(len(self._items) - 1, int(event.x / self._segment_width()))
        if index != self._hover_index:
            self._hover_index = index
            self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover_index = -1
        self._redraw()

    def _move(self, delta: int) -> None:
        values = [value for value, _ in self._items]
        try:
            index = values.index(self._value)
        except ValueError:
            index = 0
        index = max(0, min(len(values) - 1, index + delta))
        if values[index] != self._value:
            self._value = values[index]
            self._redraw()
            if self._on_change:
                self._on_change(self._value)

    def set_value(self, value: str) -> None:
        if value in [value for value, _ in self._items] and value != self._value:
            self._value = value
            self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 20)
        height = self._height
        rounded(self, 0.5, 0.5, width - 0.5, height - 0.5, 9,
                fill=theme.INPUT_BG, outline=theme.BORDER, width=1)
        segment = width / len(self._items)
        for index, (value, label) in enumerate(self._items):
            x0 = index * segment + 3
            x1 = (index + 1) * segment - 3
            active = value == self._value
            hover = index == self._hover_index and not active
            if active:
                rounded(self, x0, 3, x1, height - 3, 7,
                        fill=theme.blend(theme.ACCENT, 0.16, self._base_bg),
                        outline=theme.blend(theme.ACCENT, 0.38, self._base_bg),
                        width=1)
            elif hover:
                rounded(self, x0, 3, x1, height - 3, 7,
                        fill=theme.blend(theme.WHITE, 0.04, self._base_bg),
                        outline="", width=0)
            color = theme.ACCENT if active else theme.MUTED
            self.create_text((x0 + x1) / 2, height / 2 - 1, text=label,
                             fill=color, font=self._font)


class EntryField(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        textvariable: tk.StringVar | None = None,
        show: str | None = None,
        height: int = 46,
        bg: str | None = None,
        font: tuple | None = None,
        on_change: Callable[[str], None] | None = None,
        on_submit: Callable[[], None] | None = None,
    ) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, bg=base)
        self._base_bg = base
        self._height = height
        self._canvas = tk.Canvas(self, height=height, bg=base,
                                 highlightthickness=0, bd=0)
        self._canvas.pack(fill="x")
        self._font = font or (theme.load_fonts(master)._ui_family, -14, "normal")
        self.var = textvariable or tk.StringVar()
        self.entry = tk.Entry(
            self._canvas,
            textvariable=self.var,
            show=show or "",
            bd=0,
            relief="flat",
            bg=theme.INPUT_BG,
            fg=theme.TEXT,
            insertbackground=theme.ACCENT,
            selectbackground=theme.ACCENT_SOFT,
            selectforeground=theme.INVERSE,
            font=self._font,
            highlightthickness=0,
        )
        self._window = self._canvas.create_window(15, height / 2, anchor="w",
                                                  window=self.entry, width=120,
                                                  height=height - 18)
        self._canvas.bind("<Configure>", self._on_configure)
        self.entry.bind("<FocusIn>", lambda _e: self._draw(True))
        self.entry.bind("<FocusOut>", lambda _e: self._draw(False))
        if on_change:
            self.var.trace_add("write", lambda *_: on_change(self.var.get()))
        if on_submit:
            self.entry.bind("<Return>", lambda _e: on_submit())

    def _on_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._window, width=max(20, int(event.width) - 30))
        self._draw(self.entry.focus_get() is self.entry)

    def _draw(self, focused: bool) -> None:
        canvas = self._canvas
        canvas.delete("deco")
        width = max(canvas.winfo_width(), 20)
        height = self._height
        rounded(canvas, 0.5, 0.5, width - 0.5, height - 0.5, 10,
                fill=theme.INPUT_BG,
                outline=theme.mix(theme.BORDER, theme.ACCENT, 0.55) if focused else theme.BORDER,
                width=1, tags="deco")
        canvas.tag_lower("deco")

    def focus(self) -> None:
        self.entry.focus_set()

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)


class Pill(tk.Canvas):
    def __init__(self, master: tk.Misc, text: str, tone: str = "accent",
                 *, bg: str | None = None, font: tuple | None = None,
                 height: int = 20) -> None:
        base = bg or master.cget("bg")
        self._font = font or (theme.load_fonts(master)._ui_family, -9, "bold")
        self._text = text
        self._tone = tone
        self._base_bg = base
        width = measure(self._font, text) + 20
        super().__init__(master, width=width, height=height, bg=base,
                         highlightthickness=0, bd=0)
        color = theme.tone(tone)
        rounded(self, 0.5, 0.5, width - 0.5, height - 0.5, height / 2,
                fill=theme.blend(color, 0.12, base),
                outline=theme.blend(color, 0.32, base), width=1)
        self.create_text(width / 2, height / 2 - 1, text=text, fill=color,
                         font=self._font)


class Meter(tk.Canvas):
    """Continuous strength bar with a soft highlight."""

    def __init__(self, master: tk.Misc, *, bg: str | None = None,
                 height: int = 6) -> None:
        base = bg or master.cget("bg")
        super().__init__(master, height=height, bg=base,
                         highlightthickness=0, bd=0)
        self._height = height
        self._ratio = 0.0
        self._tone = theme.ACCENT
        self.bind("<Configure>", lambda _e: self._redraw())

    def set(self, ratio: float, tone: str) -> None:
        self._ratio = max(0.0, min(1.0, ratio))
        self._tone = tone
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 40)
        height = self._height
        rounded(self, 0, 0, width, height, height / 2,
                fill=theme.mix(theme.BORDER, theme.BG, 0.45), outline="")
        if self._ratio <= 0.0:
            return
        end = max(height, width * self._ratio)
        color = theme.tone(self._tone)
        rounded(self, 0, 0, end, height, height / 2, fill=color, outline="")
        if end > height:
            self.create_line(height / 2, 1, end - height / 2, 1,
                             fill=theme.mix(color, theme.WHITE, 0.35))


def divider(master: tk.Misc, *, pady: int = 0) -> tk.Frame:
    line = tk.Frame(master, bg=theme.HAIRLINE, height=1)
    line.pack(fill="x", pady=pady)
    return line
