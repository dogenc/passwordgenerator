"""Design tokens and fonts for the DGKN@Labs glass UI."""

from __future__ import annotations

from dataclasses import dataclass

import tkinter.font as tkfont

# Surfaces
BG = "#070B14"
BG_RAISED = "#0A101C"
GLASS_TOP = "#111A2B"
GLASS_BOTTOM = "#0C1422"
CARD_TOP = "#121C2E"
CARD_BOTTOM = "#0D1625"
INPUT_BG = "#0A1220"
SURFACE_SOLID = "#0E1626"

# Lines
BORDER = "#1C2740"
BORDER_STRONG = "#2B3B5C"
HAIRLINE = "#162033"

# Text
TEXT = "#E9EFFA"
MUTED = "#93A1BC"
DIM = "#5F6E8C"
INVERSE = "#04120F"

# Accents
ACCENT = "#5BE3CE"
ACCENT_SOFT = "#2A8C80"
ACCENT_2 = "#91A6FF"
OK = "#5BE3CE"
INFO = "#7FB2FF"
WARN = "#FFC46B"
DANGER = "#FF6F83"
WHITE = "#FFFFFF"

TONES = {
    "accent": ACCENT,
    "ok": OK,
    "info": INFO,
    "warn": WARN,
    "danger": DANGER,
    "muted": MUTED,
}

# Geometry (pixels, DPI-unaware rendering for a stable layout)
HEADER_H = 106
STATUS_H = 36
PAGE_PAD = 26
PANEL_RADIUS = 18
CARD_RADIUS = 14
PANEL_PAD = 18

# Font stacks: first available family wins. Windows ships Segoe UI/Consolas,
# Linux falls back to DejaVu, macOS to SF/Helvetica.
_UI_STACK = (
    "Segoe UI Variable Text",
    "Segoe UI",
    "Inter",
    "SF Pro Text",
    "Helvetica Neue",
    "DejaVu Sans",
    "Liberation Sans",
    "Arial",
)
_MONO_STACK = (
    "Cascadia Mono",
    "Consolas",
    "JetBrains Mono",
    "SF Mono",
    "Menlo",
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Courier New",
)


def _rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def mix(color_a: str, color_b: str, ratio: float) -> str:
    """Blend two hex colours; ratio 0 -> a, 1 -> b."""

    ratio = max(0.0, min(1.0, ratio))
    a = _rgb(color_a)
    b = _rgb(color_b)
    return "#%02X%02X%02X" % tuple(
        round(a[index] + (b[index] - a[index]) * ratio) for index in range(3)
    )


def blend(color: str, alpha: float, base: str = BG) -> str:
    """Approximate alpha compositing against an opaque background."""

    return mix(base, color, alpha)


def tone(name: str) -> str:
    return TONES.get(name, MUTED)


@dataclass(frozen=True)
class Fonts:
    ui_family: str
    mono_family: str

    def ui(self, size: int = 13, weight: str = "normal") -> tuple[str, int, str]:
        return (self.ui_family, -abs(size), weight)

    def mono(self, size: int = 15, weight: str = "normal") -> tuple[str, int, str]:
        return (self.mono_family, -abs(size), weight)

    def display(self, size: int = 34, weight: str = "bold") -> tuple[str, int, str]:
        return (self.ui_family, -abs(size), weight)


def load_fonts(root: object) -> Fonts:
    families = set(tkfont.families(root))
    ui = next((name for name in _UI_STACK if name in families), "TkDefaultFont")
    mono = next((name for name in _MONO_STACK if name in families), "TkFixedFont")
    return Fonts(ui_family=ui, mono_family=mono)
