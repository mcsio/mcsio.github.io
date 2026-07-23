#!/usr/bin/env python3
"""Generate the mcsio brand assets: favicon set + Open Graph card.

The mark is the drawdown path crossing the ladder rungs — the essay's
subject reduced to a glyph. Everything is drawn at 8x and downsampled,
because PIL's line primitives are aliased.

    python3 tools/make_brand.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
MENLO = "/System/Library/Fonts/Menlo.ttc"

GROUND = (10, 14, 19)
BLUE = (76, 143, 209)
AMBER = (217, 154, 43)
TEXT = (217, 225, 233)
MUTE = (110, 124, 138)

SS = 8  # supersample factor

# the drawdown path, normalised into the mark's box
PATH = [(0.06, 0.13), (0.44, 0.46), (0.68, 0.45), (0.80, 0.73), (0.94, 0.87)]
RUNGS_FULL = [0.46, 0.62, 0.87]
RUNGS_SMALL = [0.46, 0.87]


def font(size, bold=False):
    return ImageFont.truetype(MENLO, size, index=1 if bold else 0)


def draw_mark(size, pad_ratio=0.16, rungs=None, rung_w=None, line_w=None):
    """The glyph, on its own dark tile."""
    S = size * SS
    img = Image.new("RGB", (S, S), GROUND)
    d = ImageDraw.Draw(img)

    pad = S * pad_ratio
    box = S - 2 * pad

    def px(nx, ny):
        return (pad + nx * box, pad + ny * box)

    rungs = rungs if rungs is not None else RUNGS_FULL
    rung_w = rung_w or max(1, int(S * 0.014))
    line_w = line_w or max(1, int(S * 0.055))

    for ry in rungs:
        y = pad + ry * box
        d.line([(pad, y), (pad + box, y)], fill=BLUE, width=rung_w)

    # amber peak tick — the moment the damage was done
    tx = pad + PATH[0][0] * box
    d.line([(tx, pad * 0.55), (tx, S - pad * 0.55)], fill=AMBER,
           width=max(1, int(S * 0.020)))

    d.line([px(x, y) for x, y in PATH], fill=BLUE, width=line_w,
           joint="curve")

    return img.resize((size, size), Image.LANCZOS)


def build_icons():
    OUT.mkdir(exist_ok=True)
    specs = [
        ("favicon-16.png", 16, RUNGS_SMALL, 0.10),
        ("favicon-32.png", 32, RUNGS_SMALL, 0.12),
        ("favicon-48.png", 48, RUNGS_FULL, 0.14),
        ("apple-touch-icon.png", 180, RUNGS_FULL, 0.18),
        ("icon-192.png", 192, RUNGS_FULL, 0.16),
        ("icon-512.png", 512, RUNGS_FULL, 0.16),
    ]
    made = []
    for name, size, rungs, pad in specs:
        # heavier strokes at small sizes or the glyph dissolves
        lw = max(2, int(size * SS * (0.075 if size <= 32 else 0.055)))
        rw = max(1, int(size * SS * (0.022 if size <= 32 else 0.014)))
        img = draw_mark(size, pad_ratio=pad, rungs=rungs,
                        rung_w=rw, line_w=lw)
        img.save(OUT / name)
        made.append(name)

    ico = draw_mark(48, pad_ratio=0.12, rungs=RUNGS_SMALL,
                    rung_w=int(48 * SS * 0.020), line_w=int(48 * SS * 0.070))
    ico.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    made.append("favicon.ico")
    return made


def build_og():
    """1200x630 share card: headline over the real drawdown path."""
    W, H = 1200 * 2, 630 * 2  # 2x then downsample
    img = Image.new("RGB", (W, H), GROUND)
    d = ImageDraw.Draw(img)

    m = 96 * 2  # margin

    d.text((m, 78 * 2), "POST-MORTEM  ·  CONCENTRATED EQUITY BOOK",
           font=font(19 * 2, bold=True), fill=AMBER)

    head = ["Seventy percent of my drawdown",
            "was money I deployed after the peak."]
    y = 128 * 2
    for ln in head:
        d.text((m, y), ln, font=font(45 * 2, bold=True), fill=TEXT)
        y += 62 * 2

    # ---- chart ----
    cx0, cx1 = m, W - m
    cy0, cy1 = 300 * 2, 520 * 2
    cw, ch = cx1 - cx0, cy1 - cy0

    def px(nx, ny):
        return (cx0 + nx * cw, cy0 + ny * ch)

    tx = cx0 + PATH[0][0] * cw

    for ry, lab in zip(RUNGS_FULL, ["BRAKE", "DE-GROSS", "FULL UNWIND"]):
        yy = cy0 + ry * ch
        d.line([(cx0, yy), (cx1, yy)], fill=(30, 45, 62), width=3)
        d.text((tx + 20, yy - 36), lab, font=font(15 * 2), fill=BLUE)

    d.line([(tx, cy0 - 24), (tx, cy1 + 24)], fill=AMBER, width=4)
    d.text((tx + 16, cy0 - 44), "34% of the book deployed here, in one session",
           font=font(16 * 2), fill=AMBER)

    pts = [px(x, y) for x, y in PATH]
    d.line(pts, fill=BLUE, width=9, joint="curve")
    for cxp, cyp in pts:
        r = 11
        d.ellipse([cxp - r, cyp - r, cxp + r, cyp + r],
                  fill=GROUND, outline=BLUE, width=5)

    d.line([(m, H - 108), (W - m, H - 108)], fill=(35, 45, 56), width=3)
    d.text((m, H - 88), "mcsio.com", font=font(21 * 2, bold=True), fill=TEXT)
    tw = d.textlength("35 rules -> 12", font=font(21 * 2))
    d.text((W - m - tw, H - 88), "35 rules -> 12",
           font=font(21 * 2), fill=MUTE)

    img = img.resize((1200, 630), Image.LANCZOS)
    img.save(OUT / "og.png")
    return "og.png"


if __name__ == "__main__":
    icons = build_icons()
    og = build_og()
    for n in icons + [og]:
        p = (ROOT / "favicon.ico") if n == "favicon.ico" else (OUT / n)
        print(f"  {n:24s} {p.stat().st_size:>8,d} bytes")
