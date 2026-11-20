#!/usr/bin/env python3
"""Max-time variants: tight HH/MM, weekday top, date below time, steps bottom."""

from PIL import Image, ImageDraw, ImageFont, ImageColor
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
W, H = 126, 294
DEP = str(ROOT / "fonts" / "DepartureMono-Regular.woff2")
BG = "#24283b"
DIM = "#565f89"
RED = "#f7768e"
ORANGE = "#ff9e64"


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


def make_battery_icon(level):
    w, h, border = 44, 22, 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if level >= 2:
        return img
    hex_col = RED if level == 0 else ORANGE
    col = ImageColor.getcolor(hex_col, "RGBA")
    d = ImageDraw.Draw(img)

    for b in range(border):
        d.rectangle([b, b, w - 1 - b, h - 1 - b], outline=col, width=1)

    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        img.putpixel(pt, (0, 0, 0, 0))

    L = ["1100", "1100", "1100", "1100", "1100", "1100", "1100", "1100", "1111", "1111"]
    O = ["011110", "110011", "110011", "110011", "110011", "110011", "110011", "110011", "110011", "011110"]
    W = ["11000011", "11000011", "11000011", "11000011", "11000011", "11011011", "11011011", "01111110", "01100110", "00100100"]

    spacing = 3
    tw = len(L[0]) + spacing + len(O[0]) + spacing + len(W[0])
    th = 10
    start_x = (w - tw) // 2
    start_y = (h - th) // 2

    def draw_glyph(glyph_rows, gx, gy):
        for r, row in enumerate(glyph_rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    img.putpixel((gx + c, gy + r), col)

    cx = start_x
    draw_glyph(L, cx, start_y)
    cx += len(L[0]) + spacing
    draw_glyph(O, cx, start_y)
    cx += len(O[0]) + spacing
    draw_glyph(W, cx, start_y)
    return img


# tight vertical: 60x90 boxes, offset 70 (overlap 20, visual gap ~14px)
BW, BH = 60, 90
BX0, BX1 = 13, 53
HH_Y, MM_Y = 62, 132
WD_Y = 6  # weekday 44x20 top
DATE_Y0, DATE_Y1 = 28, 52
STEPS_Y0, STEPS_Y1 = 234, 260
BATT_W, BATT_H = 44, 22
BATT_X = (W - BATT_W) // 2
BATT_Y = 264


def build(name, tcol, wdcol, datecol, stepcol):
    out = ROOT / "faces" / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    Image.new("RGB", (W, H), BG).save(out / "0.png")
    for i in range(10):
        glyph(str(i), BW, BH, 78, tcol).save(out / f"{i + 1}.png")
    for i in range(10):
        glyph(str(i), 18, 24, 22, datecol).save(out / f"{i + 11}.png")
    glyph("/", 18, 24, 22, DIM).save(out / "21.png")
    for i in range(10):
        glyph(str(i), 20, 26, 24, stepcol).save(out / f"{i + 22}.png")
    for idx in range(6):
        make_battery_icon(idx).save(out / f"{32 + idx}.png")
    for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
        glyph(dd, 44, 20, 18, wdcol).save(out / f"{38 + i}.png")
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
            "BatteryIcon": {
                "X": BATT_X,
                "Y": BATT_Y,
                "ImageIndex": 32,
                "ImagesCount": 6,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


def build_duo(name, hhcol, mmcol, wdcol, datecol, stepcol):
    out = ROOT / "faces" / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    Image.new("RGB", (W, H), BG).save(out / "0.png")
    for i in range(10):
        glyph(str(i), BW, BH, 78, hhcol).save(out / f"{i + 1}.png")
    for i in range(10):
        glyph(str(i), 18, 24, 22, datecol).save(out / f"{i + 11}.png")
    glyph("/", 18, 24, 22, DIM).save(out / "21.png")
    for i in range(10):
        glyph(str(i), 20, 26, 24, stepcol).save(out / f"{i + 22}.png")
    for idx in range(6):
        make_battery_icon(idx).save(out / f"{32 + idx}.png")
    for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
        glyph(dd, 44, 20, 18, wdcol).save(out / f"{38 + i}.png")
    for i in range(10):
        glyph(str(i), BW, BH, 78, mmcol).save(out / f"{45 + i}.png")
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": BX0, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": BX0, "Y": MM_Y, "ImageIndex": 45, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": MM_Y, "ImageIndex": 45, "ImagesCount": 10},
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
            "BatteryIcon": {
                "X": BATT_X,
                "Y": BATT_Y,
                "ImageIndex": 32,
                "ImagesCount": 6,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


build_duo(
    "clean-night-15-duo-frost", "#ffffff", "#7aa2f7", "#7aa2f7", "#7aa2f7", "#7aa2f7"
)
build_duo(
    "clean-night-16-duo-sky", "#c0caf5", "#7dcfff", "#7aa2f7", "#7aa2f7", "#7aa2f7"
)
build_duo(
    "clean-night-17-duo-deep", "#7aa2f7", "#c0caf5", "#7aa2f7", "#7aa2f7", "#7aa2f7"
)


build("clean-night-10-blue", "#c0caf5", "#7aa2f7", "#7aa2f7", "#7aa2f7")
build("clean-night-11-mono", "#ffffff", "#c0caf5", "#c0caf5", "#ffffff")
build("clean-night-12-volt", "#FAFF00", "#7aa2f7", "#7aa2f7", "#9ece6a")
build("clean-night-13-aqua", "#7dcfff", "#565f89", "#7dcfff", "#7dcfff")
build("clean-night-14-ember", "#ff9e64", "#e0af68", "#e0af68", "#9ece6a")
