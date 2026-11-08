#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the prampa logo (SVG + PNG) used by the menu HUD."""

from PIL import Image, ImageDraw

S = 512          # output size
SS = 4           # supersampling
C = S * SS

ACCENT = (124, 92, 255)     # #7C5CFF
CYAN = (0, 208, 255)        # #00D0FF

# geometry in 512-space
STEM = (176, 104, 246, 424)          # x1, y1, x2, y2
BOWL = (150, 100, 342, 292)          # outer ellipse bbox -> centre (246,196) r=96
HOLE = (208, 158, 284, 234)          # counter bbox -> centre (246,196) r=38
RADIUS = 120                         # outer squircle radius


def scale_box(box):
    return tuple(int(v * SS) for v in box)


def build_mask():
    mask = Image.new("L", (C, C), 0)
    draw = ImageDraw.Draw(mask)

    x1, y1, x2, y2 = scale_box(STEM)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=35 * SS, fill=255)

    draw.pieslice(scale_box(BOWL), start=-90, end=90, fill=255)
    draw.pieslice(scale_box(HOLE), start=-90, end=90, fill=0)

    return mask


def build_gradient():
    small = Image.new("RGB", (S, S))
    px = small.load()

    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * (S - 1))
            px[x, y] = (
                round(ACCENT[0] + (CYAN[0] - ACCENT[0]) * t),
                round(ACCENT[1] + (CYAN[1] - ACCENT[1]) * t),
                round(ACCENT[2] + (CYAN[2] - ACCENT[2]) * t),
            )

    return small.resize((C, C), Image.BICUBIC)


def build_png():
    glyph_mask = build_mask().resize((S, S), Image.LANCZOS)
    gradient = build_gradient().resize((S, S), Image.LANCZOS)

    squircle = Image.new("L", (S * SS, S * SS), 0)
    ImageDraw.Draw(squircle).rounded_rectangle(
        [0, 0, S * SS - 1, S * SS - 1], radius=RADIUS * SS, fill=255
    )
    squircle = squircle.resize((S, S), Image.LANCZOS)

    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(gradient, (0, 0), squircle)

    white = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    transparent = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas = Image.alpha_composite(canvas, Image.composite(white, transparent, glyph_mask))

    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [2, 2, S - 3, S - 3], radius=RADIUS - 2,
        outline=(255, 255, 255, 45), width=3,
    )
    canvas = Image.alpha_composite(canvas, border)

    canvas.save("prampa-logo.png", optimize=True)
    canvas.resize((128, 128), Image.LANCZOS).save("prampa-logo-128.png", optimize=True)
    canvas.resize((64, 64), Image.LANCZOS).save("prampa-logo-64.png", optimize=True)
    return canvas


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="prampa">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#7C5CFF"/>
      <stop offset="1" stop-color="#00D0FF"/>
    </linearGradient>
    <mask id="p">
      <rect width="512" height="512" fill="#000"/>
      <rect x="176" y="104" width="70" height="320" rx="35" fill="#fff"/>
      <path d="M246 100 A96 96 0 0 1 246 292 Z" fill="#fff"/>
      <path d="M246 158 A38 38 0 0 1 246 234 Z" fill="#000"/>
    </mask>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="14" flood-color="#7C5CFF" flood-opacity="0.45"/>
    </filter>
  </defs>
  <g filter="url(#glow)">
    <rect width="512" height="512" rx="120" fill="url(#g)"/>
  </g>
  <g mask="url(#p)">
    <rect width="512" height="512" fill="#ffffff"/>
  </g>
  <rect x="2" y="2" width="508" height="508" rx="118" fill="none"
        stroke="#ffffff" stroke-opacity="0.16" stroke-width="3"/>
</svg>
"""


if __name__ == "__main__":
    with open("prampa-logo.svg", "w", encoding="utf-8", newline="\n") as f:
        f.write(SVG)
    img = build_png()
    print("wrote prampa-logo.svg, prampa-logo.png (%dx%d), -128, -64" % img.size)
