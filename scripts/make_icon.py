#!/usr/bin/env python3
"""Generate the DGKN@Labs PWGen application icon (development tool).

Requires Pillow; the shipped application does not depend on it.
Run from the repository root:  python scripts/make_icon.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter

ACCENT = (91, 227, 206)
ACCENT_DIM = (43, 128, 120)
BG_TOP = (16, 27, 45)
BG_BOTTOM = (7, 11, 20)
BORDER = (43, 59, 92)


def gradient(size: int) -> Image.Image:
    image = Image.new("RGB", (1, size))
    for y in range(size):
        ratio = y / max(1, size - 1)
        image.putpixel(
            (0, y),
            tuple(
                round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * ratio)
                for i in range(3)
            ),
        )
    return image.resize((size, size), Image.NEAREST)


def make_icon(size: int = 256) -> Image.Image:
    scale = size / 256
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    body = gradient(size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (2, 2, size - 2, size - 2), radius=int(54 * scale), fill=255
    )
    canvas.paste(body, (0, 0), mask)

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        (int(56 * scale), int(40 * scale), int(200 * scale), int(184 * scale)),
        fill=ACCENT + (46,),
    )
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(20 * scale)))

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (2, 2, size - 2, size - 2), radius=int(54 * scale),
        outline=BORDER + (255,), width=max(1, int(2 * scale)),
    )
    draw.line(
        (int(64 * scale), int(6 * scale), int(192 * scale), int(6 * scale)),
        fill=(255, 255, 255, 26), width=max(1, int(2 * scale)),
    )

    shield = [
        (128, 54), (188, 82), (180, 148), (128, 198),
        (76, 148), (68, 82),
    ]
    points = [(x * scale, y * scale) for x, y in shield]
    draw.polygon(points, fill=ACCENT + (28,), outline=ACCENT + (235,),
                 width=max(2, int(7 * scale)))

    hole = [
        (128, 104), (151, 127), (143, 171), (113, 171), (105, 127),
    ]
    hole_points = [(x * scale, y * scale) for x, y in hole]
    draw.polygon(hole_points, fill=BG_BOTTOM + (255,))
    draw.ellipse(
        (int(118 * scale), int(96 * scale), int(138 * scale), int(128 * scale)),
        fill=BG_BOTTOM + (255,), outline=ACCENT_DIM + (255,),
        width=max(1, int(2 * scale)),
    )

    # Specular rim on the shield's left edge.
    draw.line(
        [(x * scale, y * scale) for x, y in [(76, 148), (68, 82), (128, 54)]],
        fill=(255, 255, 255, 40), width=max(1, int(2 * scale)),
    )
    return canvas


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(root, "assets")
    os.makedirs(assets, exist_ok=True)
    icon = make_icon(256)
    icon.save(os.path.join(assets, "pwgen.png"))
    icon.save(
        os.path.join(assets, "pwgen.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("assets/pwgen.png und assets/pwgen.ico erzeugt")


if __name__ == "__main__":
    main()
