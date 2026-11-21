#!/usr/bin/env python3
"""VELMARIS — a travel poster for a place that does not exist.

Draws a 1024x1024 travel poster entirely in code (Pillow, no network,
no external assets except the bundled display font) and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT when set).

The place: VELMARIS, a floating island-city above a sea of clouds at
golden hour. One landmark — the great ringed lighthouse on the island's
crown — one promise: a stay above the clouds, where the waterfalls fall
up into the sky and the sun never quite sets.
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
MAX_BYTES = 1_048_576
PLACE = "VELMARIS"

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MAKEFUN_OUTPUT", "/output/entry.png"))

# ---------------------------------------------------------------- palette
DEEP_TEAL = (16, 58, 74)
MID_TEAL = (38, 106, 122)
DUSK_BLUE = (74, 138, 150)
AMBER = (232, 165, 75)
GOLD = (247, 200, 115)
SUN_CORE = (255, 233, 168)
SUN_HALO = (255, 190, 90)
CREAM = (255, 246, 220)
CLOUD_LIT = (255, 239, 196)
CLOUD_SHADE = (196, 168, 132)
ISLAND_GREEN = (74, 122, 74)
ISLAND_GREEN_DK = (46, 88, 58)
ISLAND_GOLD = (198, 158, 74)
ROCK = (96, 74, 58)
ROCK_DK = (62, 48, 40)
ROCK_LT = (138, 104, 78)
TOWER_WHITE = (250, 240, 214)
TOWER_GOLD = (214, 158, 62)
INK = (24, 42, 54)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_gradient():
    """Vertical sky: deep teal at the top, amber at the horizon."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    stops = [
        (0.00, DEEP_TEAL),
        (0.30, MID_TEAL),
        (0.52, DUSK_BLUE),
        (0.66, AMBER),
        (0.78, GOLD),
        (1.00, (250, 214, 140)),
    ]
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                d.line([(0, y), (W, y)], fill=lerp(c0, c1, (t - t0) / (t1 - t0)))
                break
    return img


def soft_disc(layer, cx, cy, r, color, blur):
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return layer.filter(ImageFilter.GaussianBlur(blur))


def draw_sun(base):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = soft_disc(glow, 790, 630, 200, (255, 186, 92, 70), 60)
    glow = soft_disc(glow, 790, 630, 120, (255, 214, 130, 110), 40)
    base.alpha_composite(glow)
    d = ImageDraw.Draw(base)
    d.ellipse([790 - 80, 630 - 80, 790 + 80, 630 + 80], fill=SUN_CORE + (255,))
    d.ellipse([790 - 58, 630 - 58, 790 + 58, 630 + 58], fill=(255, 244, 200, 255))
    return base


def draw_distant_islets(base):
    """Two small hazy islets far away, for depth."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # left islet
    d.polygon([(120, 470), (250, 470), (215, 520), (185, 545), (155, 520)],
              fill=(58, 96, 104, 200))
    d.polygon([(150, 470), (220, 470), (205, 452), (185, 440), (168, 452)],
              fill=(88, 128, 118, 200))
    d.rectangle([182, 408, 190, 444], fill=(240, 224, 180, 220))
    # right islet
    d.polygon([(830, 430), (950, 430), (918, 478), (890, 500), (862, 478)],
              fill=(58, 96, 104, 200))
    d.polygon([(858, 430), (922, 430), (908, 414), (890, 404), (874, 414)],
              fill=(88, 128, 118, 200))
    d.rectangle([887, 378, 894, 406], fill=(240, 224, 180, 220))
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    base.alpha_composite(layer)
    return base


def draw_airship(base):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # balloon
    d.ellipse([150, 268, 268, 330], fill=(196, 84, 62, 255))
    d.ellipse([150, 268, 268, 330], outline=(140, 52, 40, 255), width=3)
    d.arc([170, 272, 248, 326], 200, 340, fill=(232, 150, 110, 255), width=5)
    # gold band around the balloon
    d.arc([150, 282, 268, 316], 0, 360, fill=(232, 178, 90, 255), width=6)
    # gondola
    d.polygon([(196, 332), (224, 332), (218, 352), (202, 352)],
              fill=(96, 62, 40, 255))
    d.line([(186, 330), (196, 332)], fill=(96, 62, 40, 255), width=2)
    d.line([(234, 330), (224, 332)], fill=(96, 62, 40, 255), width=2)
    # little flag
    d.line([(209, 268), (209, 244)], fill=(96, 62, 40, 255), width=2)
    d.polygon([(209, 244), (232, 250), (209, 256)], fill=(247, 200, 115, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    base.alpha_composite(layer)
    return base


def draw_birds(base):
    d = ImageDraw.Draw(base)
    for cx, cy, s in [(330, 330, 14), (372, 306, 11), (820, 300, 12),
                      (860, 340, 9), (150, 420, 10)]:
        d.arc([cx - s, cy - s // 2, cx, cy + s // 2], 200, 340,
              fill=(30, 48, 58, 220), width=3)
        d.arc([cx, cy - s // 2, cx + s, cy + s // 2], 200, 340,
              fill=(30, 48, 58, 220), width=3)
    return base


def draw_island(base):
    """The landmark: VELMARIS, the floating island with its lighthouse."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # --- rocky underside: inverted cone with facets
    d.polygon([(238, 512), (786, 512), (512, 806)],
              fill=ROCK + (255,))
    # facet shading
    d.polygon([(238, 512), (512, 512), (512, 806)], fill=ROCK_LT + (255,))
    d.polygon([(512, 512), (786, 512), (512, 806)], fill=ROCK_DK + (255,))
    # strata lines
    for i, y in enumerate((560, 610, 662, 716)):
        t = (y - 512) / (806 - 512)
        half = (786 - 238) / 2 * (1 - t)
        d.line([(512 - half + 14, y), (512 + half - 14, y)],
               fill=(52, 40, 34, 160), width=4)
    # rocky teeth along the rim
    rng = random.Random(7)
    for x in range(250, 780, 26):
        depth = rng.randint(10, 30)
        d.polygon([(x, 512), (x + 13, 512), (x + 6, 512 + depth)],
                  fill=ROCK_DK + (255,))

    # --- green crown terraces
    d.ellipse([222, 470, 802, 540], fill=ISLAND_GREEN_DK + (255,))
    d.ellipse([240, 452, 784, 522], fill=ISLAND_GREEN + (255,))
    d.ellipse([268, 440, 756, 506], fill=(96, 142, 82, 255))
    # golden meadow band
    d.ellipse([300, 448, 724, 496], fill=ISLAND_GOLD + (255,))
    d.ellipse([330, 442, 694, 486], fill=(216, 178, 96, 255))

    # --- small cypress trees on the crown
    for x, h in [(300, 34), (336, 26), (700, 30), (736, 24), (664, 20)]:
        d.polygon([(x - 7, 470), (x + 7, 470), (x, 470 - h)],
                  fill=(34, 66, 44, 255))
        d.line([(x, 470), (x, 474)], fill=(34, 66, 44, 255), width=3)

    # --- the lighthouse: tapered white tower, gold bands, glowing lantern
    tx, top, bot = 560, 246, 470
    d.polygon([(tx - 26, bot), (tx + 26, bot), (tx + 15, top + 34),
               (tx - 15, top + 34)], fill=TOWER_WHITE + (255,))
    d.polygon([(tx - 26, bot), (tx + 26, bot), (tx + 22, bot - 26),
               (tx - 22, bot - 26)], fill=(226, 210, 178, 255))
    for by in (330, 386):
        half = 26 - (bot - by) * (11 / (bot - (top + 34)))
        d.polygon([(tx - half, by - 7), (tx + half, by - 7),
                   (tx + half - 1, by + 7), (tx - half + 1, by + 7)],
                  fill=TOWER_GOLD + (255,))
    # gallery + lantern room
    d.rectangle([tx - 22, top + 18, tx + 22, top + 34], fill=(52, 44, 40, 255))
    d.rectangle([tx - 15, top, tx + 15, top + 18], fill=(255, 226, 140, 255))
    d.rectangle([tx - 15, top, tx + 15, top + 18], outline=(52, 44, 40, 255),
                width=2)
    d.polygon([(tx - 19, top), (tx + 19, top), (tx, top - 16)],
              fill=(196, 84, 62, 255))
    # beacon glow + rays sweeping sideways across the sky, clear of the title
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = soft_disc(glow, tx, top + 9, 46, (255, 224, 130, 130), 18)
    layer.alpha_composite(glow)
    d = ImageDraw.Draw(layer)
    for ang in (-72, -52, 52, 72):
        rad = math.radians(ang)
        x2 = tx + int(math.sin(rad) * 175)
        y2 = top + 9 - int(math.cos(rad) * 175)
        d.polygon([(tx, top + 9), (x2 - 10, y2 - 12), (x2 + 10, y2 + 12)],
                  fill=(255, 232, 160, 50))
    # door + window
    d.rectangle([tx - 6, bot - 22, tx + 6, bot], fill=(52, 44, 40, 255))
    d.ellipse([tx - 4, 300, tx + 4, 312], fill=(52, 44, 40, 255))

    layer = layer.filter(ImageFilter.GaussianBlur(0.5))
    base.alpha_composite(layer)
    return base


def draw_waterfalls(base):
    """Three falls spilling off the island rim, dissolving into cloud."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(21)
    for x0, wdt, length in [(318, 20, 260), (452, 15, 300), (648, 18, 280)]:
        pts = []
        for i in range(0, length + 1, 12):
            pts.append((x0 + rng.randint(-2, 2) + int(3 * math.sin(i / 40)),
                        512 + i))
        d.line(pts, fill=(238, 248, 252, 200), width=wdt)
        d.line([(x, y + 2) for x, y in pts], fill=(255, 255, 255, 150),
               width=max(4, wdt // 3))
        # mist puff where it meets the cloud
        d.ellipse([x0 - 26, 512 + length - 12, x0 + 26, 512 + length + 26],
                  fill=(255, 246, 224, 140))
        # bright lip where the fall leaves the rim
        d.ellipse([x0 - wdt // 2, 506, x0 + wdt // 2, 520],
                  fill=(255, 255, 255, 200))
    layer = layer.filter(ImageFilter.GaussianBlur(3))
    base.alpha_composite(layer)
    return base


def draw_cloud_sea(base):
    """The sea of clouds the island floats above."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(42)
    # shadowed under-layer — warm and light, so the sea stays bright
    for _ in range(30):
        x = rng.randint(-60, W)
        y = rng.randint(810, 990)
        r = rng.randint(46, 110)
        d.ellipse([x - r, y - r // 3, x + r, y + r // 3],
                  fill=(226, 198, 158, 255))
    # lit tops
    for _ in range(64):
        x = rng.randint(-60, W)
        y = rng.randint(760, 940)
        r = rng.randint(40, 110)
        d.ellipse([x - r, y - r // 3, x + r, y + r // 3],
                  fill=CLOUD_LIT + (255,))
    # bright crests catching the sun
    for _ in range(34):
        x = rng.randint(0, W)
        y = rng.randint(740, 860)
        r = rng.randint(22, 60)
        d.ellipse([x - r, y - r // 4, x + r, y + r // 4],
                  fill=(255, 252, 238, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    base.alpha_composite(layer)
    # soft horizon haze where cloud meets sky
    haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    hd.rectangle([0, 730, W, 800], fill=(255, 226, 160, 60))
    haze = haze.filter(ImageFilter.GaussianBlur(24))
    base.alpha_composite(haze)
    return base


def title_font(size):
    for path in (HERE / "fonts" / "NotoSerifDisplay-Black.ttf",
                 Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"),
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")):
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue
    return ImageFont.load_default(size)


def draw_title(base):
    """The place name, letterspaced, in the upper sky — the only text."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = 118
    font = title_font(size)
    tracking = 26
    widths = [d.textlength(ch, font=font) for ch in PLACE]
    total = sum(widths) + tracking * (len(PLACE) - 1)
    x = (W - total) // 2
    y = 78
    # soft shadow, then cream letters
    for dx, dy, col in ((5, 7, (18, 36, 48, 140)), (0, 0, CREAM + (255,))):
        cx = x + dx
        for ch, wch in zip(PLACE, widths):
            d.text((cx, y + dy), ch, font=font, fill=col)
            cx += wch + tracking
    # thin gold rule beneath the name, echoing the frame
    rule_y = y + size + 34
    d.line([(x + 40, rule_y), (x + total - 40, rule_y)],
           fill=(247, 200, 115, 220), width=3)
    # small sun-mark centred on the rule
    mx = W // 2
    d.ellipse([mx - 7, rule_y - 7, mx + 7, rule_y + 7],
              fill=(247, 200, 115, 255))
    base.alpha_composite(layer)
    return base


def draw_frame(base):
    d = ImageDraw.Draw(base)
    d.rectangle([26, 26, W - 27, H - 27], outline=CREAM + (255,), width=7)
    d.rectangle([44, 44, W - 45, H - 45], outline=(247, 200, 115, 200), width=2)
    return base


def build():
    img = sky_gradient().convert("RGBA")
    img = draw_sun(img)
    img = draw_distant_islets(img)
    img = draw_airship(img)
    img = draw_birds(img)
    img = draw_island(img)
    img = draw_waterfalls(img)
    img = draw_cloud_sea(img)
    img = draw_title(img)
    img = draw_frame(img)
    return img.convert("RGB")


def save(img):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    if OUT.stat().st_size > MAX_BYTES:
        pal = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        pal.save(OUT, format="PNG", optimize=True)
    if OUT.stat().st_size > MAX_BYTES:
        img.save(OUT, format="JPEG", quality=88, optimize=True)
    return OUT.stat().st_size


def main():
    img = build()
    size = save(img)
    print(f"wrote {OUT} {img.size[0]}x{img.size[1]} {size} bytes")


if __name__ == "__main__":
    main()
