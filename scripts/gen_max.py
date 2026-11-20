#!/usr/bin/env python3
"""Max-time face: time as big as possible + date top + weekday + steps bottom."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
W, H = 126, 294
DEP = "/home/karoly/projects/Physiquinator/Physiquinator.UI/wwwroot/fonts/DepartureMono-Regular.woff2"
BG = "#24283b"
FG = "#c0caf5"
BLUE = "#7aa2f7"
GREEN = "#9ece6a"
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


name = "clean-night-09-max"
out = ROOT / name
out.mkdir(exist_ok=True)
for p in out.glob("*.png"):
    p.unlink()
Image.new("RGB", (W, H), BG).save(out / "0.png")

# big time 60x90. Max width: 60*2+2=122 fits 126
BW, BH = 60, 90
BX0, BX1 = 13, 53
HH_Y, MM_Y = 62, 142
for i in range(10):
    glyph(str(i), BW, BH, 78, FG).save(out / f"{i + 1}.png")
# date small 18x24 top
for i in range(10):
    glyph(str(i), 18, 24, 22, BLUE).save(out / f"{i + 11}.png")
glyph("/", 18, 24, 22, DIM).save(out / "21.png")
# steps small 20x26 bottom
for i in range(10):
    glyph(str(i), 20, 26, 24, GREEN).save(out / f"{i + 22}.png")
# battery low icons 32x12, 6 levels
for idx in range(6):
    img = Image.new("RGBA", (32, 12), (0, 0, 0, 0))
    if idx < 2:
        d = ImageDraw.Draw(img)
        col = RED if idx == 0 else ORANGE
        d.rectangle([0, 1, 26, 10], outline=col, width=2)
        d.rectangle([27, 4, 30, 7], fill=col)
        fw = 5 if idx == 0 else 12
        d.rectangle([3, 4, 3 + fw, 7], fill=col)
        if idx == 0:
            try:
                f = F(10)
                d.text((11, 0), "!", font=f, fill=col)
            except:
                pass
    img.save(out / f"{32 + idx}.png")
# weekday text 44x20
for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
    glyph(dd, 44, 20, 18, BLUE).save(out / f"{38 + i}.png")

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
                    "TopLeftY": 6,
                    "BottomRightX": 121,
                    "BottomRightY": 30,
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
        "ENWeekDays": {"X": 41, "Y": 32, "ImageIndex": 38, "ImagesCount": 7},
    },
    "Activity": {
        "Steps": {
            "Number": {
                "TopLeftX": 5,
                "TopLeftY": 262,
                "BottomRightX": 121,
                "BottomRightY": 288,
                "Alignment": "Center",
                "SpacingX": 1,
                "SpacingY": 0,
                "ImageIndex": 22,
                "ImagesCount": 10,
            }
        }
    },
    "Battery": {"BatteryIcon": {"X": 47, "Y": 250, "ImageIndex": 32, "ImagesCount": 6}},
}
(out / "watchface.json").write_text(json.dumps(js, indent=2))
print(name, len(list(out.glob("*.png"))), f"HH{HH_Y} MM{MM_Y} {BW}x{BH}")
