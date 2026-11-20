#!/usr/bin/env python3
"""Clean centered Tokyo Night: time exactly centered, date top, steps bottom,
battery low-icon only, weekday prototypes."""

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
CYAN = "#7dcfff"
RED = "#f7768e"
ORANGE = "#ff9e64"
DIM = "#565f89"


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


BIG_W, BIG_H = 54, 80
BX0, BX1 = 19, 53
HH_Y, MM_Y = (
    65,
    133,
)  # tight rows: offset 68, visual gap ~20px; block 65..213
SM_W, SM_H = 20, 28
DATE_Y0, DATE_Y1 = 8, 36
STEPS_Y0, STEPS_Y1 = 258, 286
BATT_X, BATT_Y = 47, 43  # gap between date top and time


def base_images(out):
    for p in out.glob("*.png"):
        p.unlink()
    Image.new("RGB", (W, H), BG).save(out / "0.png")
    for i in range(10):
        glyph(str(i), BIG_W, BIG_H, 66, FG).save(out / f"{i + 1}.png")
    for i in range(10):
        glyph(str(i), SM_W, SM_H, 24, BLUE).save(out / f"{i + 11}.png")
    glyph("/", SM_W, SM_H, 24, DIM).save(out / "21.png")
    for i in range(10):
        glyph(str(i), SM_W, SM_H, 24, GREEN).save(out / f"{i + 22}.png")
    # battery low icons 32..37 (6): 0 red critical, 1 orange low, 2-5 transparent
    for idx in range(6):
        img = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
        if idx < 2:
            d = ImageDraw.Draw(img)
            col = RED if idx == 0 else ORANGE
            d.rectangle([0, 2, 26, 13], outline=col, width=2)
            d.rectangle([27, 5, 30, 10], fill=col)
            fill = 5 if idx == 0 else 12
            d.rectangle([3, 5, 3 + fill, 10], fill=col)
            if idx == 0:
                f = F(12)
                d.text((11, 1), "!", font=f, fill=col)
        img.save(out / f"{32 + idx}.png")


def time_block():
    return {
        "Hours": {
            "Tens": {"X": BX0, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": BX1, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
        },
        "Minutes": {
            "Tens": {"X": BX0, "Y": MM_Y, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": BX1, "Y": MM_Y, "ImageIndex": 1, "ImagesCount": 10},
        },
    }


def date_top():
    return {
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
        }
    }


def steps_bottom():
    return {
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
    }


def batt_low():
    return {
        "BatteryIcon": {"X": BATT_X, "Y": BATT_Y, "ImageIndex": 32, "ImagesCount": 6}
    }


def write_face(name, parts):
    out = ROOT / name
    out.mkdir(exist_ok=True)
    base_images(out)
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": time_block(),
    }
    for k, v in parts.items():
        js[k] = v
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


write_face("clean-night-01-time", {"Battery": batt_low()})
write_face("clean-night-02-date", {"Date": date_top(), "Battery": batt_low()})
write_face("clean-night-03-steps", {"Activity": steps_bottom(), "Battery": batt_low()})
write_face(
    "clean-night-04-duo",
    {"Date": date_top(), "Activity": steps_bottom(), "Battery": batt_low()},
)


# 05 pulse bottom instead of steps (same slot, red digits)
def pulse_bottom_face():
    name = "clean-night-05-pulse"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    base_images(out)
    # recolor 22-31 to red for pulse
    for i in range(10):
        glyph(str(i), SM_W, SM_H, 24, RED).save(out / f"{i + 22}.png")
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": time_block(),
        "Activity": {
            "Pulse": {
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
        "Battery": batt_low(),
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, "pulse")


pulse_bottom_face()

# 06 trio: date top + steps bottom + battery icon (no batt numbers)
write_face(
    "clean-night-06-trio",
    {"Date": date_top(), "Activity": steps_bottom(), "Battery": batt_low()},
)


# 07 weekday text (ENWeekDays): top strip MON..SUN + steps bottom
def weekday_text_face():
    name = "clean-night-07-weekday"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    base_images(out)
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    for i, dd in enumerate(days):
        glyph(dd, 40, 20, 18, BLUE).save(out / f"{38 + i}.png")
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": time_block(),
        "Date": {"ENWeekDays": {"X": 43, "Y": 10, "ImageIndex": 38, "ImagesCount": 7}},
        "Activity": steps_bottom(),
        "Battery": batt_low(),
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, "weekday-text")


weekday_text_face()


# 08 weekday dots (WeekDaysIcons): 7 dots row top, date bottom
def weekday_dots_face():
    name = "clean-night-08-dots"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    base_images(out)
    xs = [23 + i * 12 for i in range(7)]
    for i, x in enumerate(xs):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([1, 1, 8, 8], outline=CYAN, width=2)
        d.ellipse([3, 3, 6, 6], fill=CYAN)
        img.save(out / f"{38 + i}.png")
    names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    wd = {
        n: {"X": x, "Y": 12, "ImageIndex": 38 + i}
        for n, (x, i) in zip(names, zip(xs, range(7)))
    }
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": time_block(),
        "WeekDaysIcons": wd,
        "Date": {
            "MonthAndDayAndYear": {
                "OneLine": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": STEPS_Y0,
                        "BottomRightX": 121,
                        "BottomRightY": STEPS_Y1,
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
            }
        },
        "Battery": batt_low(),
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, "dots")


weekday_dots_face()
