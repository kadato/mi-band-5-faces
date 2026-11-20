#!/usr/bin/env python3
"""Build clean-night-18-custom.bin from custom-01.json (user share-back).

Fitted layout (band is only 126x294, so requested sizes are capped to fit):
- weekday 44x20 top, date below it, big stacked HH/MM, steps + low-only
  battery icon below each other at the bottom.
- rowGap (preview px) -> MM offset adjustment (band px = rowGap/2).
- Battery % text and goal bar omitted (both off in spec); battery shows
  ONLY as low/critical icon, hidden above ~30% via transparent levels.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
SPEC = json.loads((ROOT / "custom-01.json").read_text())
W, H = 126, 294
DEP = "/home/karoly/projects/Physiquinator/Physiquinator.UI/wwwroot/fonts/DepartureMono-Regular.woff2"
DIM = "#565f89"
RED = "#f7768e"
ORANGE = "#ff9e64"

BG = SPEC["bg"]
G = SPEC["groups"]
TCOL = G["hh"]["color"]
WD = G["wd"]["color"]
DATEC = G["dt"]["color"]
STEPC = G["st"]["color"]


def F(s):
    return ImageFont.truetype(DEP, s)


def glyph(ch, w, h, size, color):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = F(size)
    bb = d.textbbox((0, 0), ch, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]), ch, font=f, fill=color)
    return img


# ---- fitted geometry (see docstring) ----
BW, BH = 60, 90  # biggest digit boxes that fit with date+steps
BX0, BX1 = 13, 53  # tight: 4px visual gap
HH_Y = 54
# Unified gap mapping (band px): MM offset = 80 + rowGap/2.
# rowGap comes from the studio slider (preview px, ÷2 = band px).
MM_Y = HH_Y + 80 + SPEC.get("rowGap", 0) // 2  # rowGap -30 -> offset 55
WD_Y, WD_W, WD_H = 4, 44, 20
DATE_Y0, DATE_Y1 = 28, 52
STEPS_Y0, STEPS_Y1 = 244, 270
BATT_X, BATT_Y, BATT_W, BATT_H = 31, 270, 64, 20
print(
    f"time boxes {BW}x{BH} HH_Y={HH_Y} MM_Y={MM_Y} (spec size {G['hh']['size']}px capped to fit)"
)

name = "clean-night-18-custom"
out = ROOT / name
out.mkdir(exist_ok=True)
for p in out.glob("*.png"):
    p.unlink()

Image.new("RGB", (W, H), BG).save(out / "0.png")
for i in range(10):
    glyph(str(i), BW, BH, 78, TCOL).save(out / f"{i + 1}.png")
for i in range(10):
    glyph(str(i), 18, 24, 22, DATEC).save(out / f"{i + 11}.png")
glyph("/", 18, 24, 22, DIM).save(out / "21.png")
for i in range(10):
    glyph(str(i), 20, 26, 24, STEPC).save(out / f"{i + 22}.png")
for idx in range(6):
    img = Image.new("RGBA", (BATT_W, BATT_H), (0, 0, 0, 0))
    if idx < 2:
        d = ImageDraw.Draw(img)
        col = RED if idx == 0 else ORANGE
        d.rectangle([0, 0, 54, 15], outline=col, width=2)
        d.rectangle([55, 4, 61, 11], fill=col)
        fw = 8 if idx == 0 else 20
        d.rectangle([3, 3, 3 + fw, 12], fill=col)
        fnt = F(11)
        txt = "LOW"
        bb = d.textbbox((0, 0), txt, font=fnt)
        tw = bb[2] - bb[0]
        tx = 3 + fw + 4
        d.text((tx - bb[0], 2 - bb[1]), txt, font=fnt, fill=RED)
    img.save(out / f"{32 + idx}.png")
for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
    glyph(dd, WD_W, WD_H, 18, WD).save(out / f"{38 + i}.png")

js = {
    "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
    "Time": {
        "Hours": {
            "Tens": {"X": BX0, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": BX1, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
        },
        "Minutes": {
            "Tens": {"X": BX0, "Y": MM_Y, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": BX1, "Y": MM_Y, "ImageIndex": 1, "ImagesCount": 10},
        },
    },
    "Date": {
        "MonthAndDayAndYear": {
            "OneLine": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": DATE_Y0,
                    "BottomRightX": 121,
                    "BottomRightY": DATE_Y1,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 11,
                    "ImagesCount": 10,
                },
                "DelimiterImageIndex": 21,
            },
            "TwoDigitsMonth": True,
            "TwoDigitsDay": True,
        },
        "ENWeekDays": {"X": 41, "Y": WD_Y, "ImageIndex": 38, "ImagesCount": 7},
    },
    "Activity": {
        "Steps": {
            "Number": {
                "TopLeftX": 5,
                "TopLeftY": STEPS_Y0,
                "BottomRightX": 121,
                "BottomRightY": STEPS_Y1,
                "Alignment": "Center",
                "SpacingX": 1,
                "SpacingY": 0,
                "ImageIndex": 22,
                "ImagesCount": 10,
            }
        }
    },
    "Battery": {
        "BatteryIcon": {"X": BATT_X, "Y": BATT_Y, "ImageIndex": 32, "ImagesCount": 6}
    },
}
(out / "watchface.json").write_text(json.dumps(js, indent=2))
print(name, len(list(out.glob("*.png"))), "images")
