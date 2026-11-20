#!/usr/bin/env python3
"""Clean Tokyo Night series: huge centered HH/MM, no labels."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
W, H = 126, 294
DEP = str(ROOT / "fonts" / "DepartureMono-Regular.woff2")
BG = "#24283b"
FG = "#c0caf5"


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


def block(w, h, c):
    return Image.new("RGBA", (w, h), c)


BIG_W, BIG_H = 54, 80
SM_W, SM_H = 20, 30
BIG_X0, BIG_X1 = 6, 66  # 54*2+6=114, margins 6


def build(name, accent, accent2, secondary=None):
    """
    secondary: None | ("date", delim="/", color) | ("steps",) | ("battery", with_bar bool)
               | ("pulse",) | ("trio",)
    """
    out = ROOT / "faces" / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    Image.new("RGB", (W, H), BG).save(out / "0.png")
    for i in range(10):
        glyph(str(i), BIG_W, BIG_H, 66, FG).save(out / f"{i + 1}.png")
    # secondary digits 11-20
    scol = {
        "date": "#7aa2f7",
        "steps": "#9ece6a",
        "battery": "#7dcfff",
        "pulse": "#f7768e",
    }.get(
        secondary[0] if isinstance(secondary, tuple) else (secondary or "date"),
        "#7aa2f7",
    )
    if secondary == "trio":
        # need 3 colors: date blue 11-20, steps green 22-31, batt cyan 32-41 (contiguous)
        for i in range(10):
            glyph(str(i), SM_W, SM_H, 24, "#7aa2f7").save(out / f"{i + 11}.png")
        glyph("/", SM_W, SM_H, 24, "#565f89").save(out / "21.png")
        for i in range(10):
            glyph(str(i), SM_W, SM_H, 24, "#9ece6a").save(out / f"{i + 22}.png")
        for i in range(10):
            glyph(str(i), SM_W, SM_H, 24, "#7dcfff").save(out / f"{i + 32}.png")
        glyph("%", 22, SM_H, 20, "#7dcfff").save(out / "42.png")
    elif secondary:
        for i in range(10):
            glyph(str(i), SM_W, SM_H, 24, scol).save(out / f"{i + 11}.png")
        if secondary == "date":
            glyph("/", SM_W, SM_H, 24, "#565f89").save(out / "21.png")
        if secondary in ("battery", "battery-bar"):
            glyph("%", 22, SM_H, 20, scol).save(out / "21.png")

    # vertical centering
    if secondary is None:
        hh_y, mm_y = 65, 149  # block 164 centered
        js_time = {
            "Hours": {
                "Tens": {"X": BIG_X0, "Y": hh_y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BIG_X1, "Y": hh_y, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": BIG_X0, "Y": mm_y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BIG_X1, "Y": mm_y, "ImageIndex": 1, "ImagesCount": 10},
            },
        }
        js = {
            "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
            "Time": js_time,
        }
    elif secondary == "trio":
        hh_y, mm_y = 22, 106
        js = {
            "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
            "Time": {
                "Hours": {
                    "Tens": {
                        "X": BIG_X0,
                        "Y": hh_y,
                        "ImageIndex": 1,
                        "ImagesCount": 10,
                    },
                    "Ones": {
                        "X": BIG_X1,
                        "Y": hh_y,
                        "ImageIndex": 1,
                        "ImagesCount": 10,
                    },
                },
                "Minutes": {
                    "Tens": {
                        "X": BIG_X0,
                        "Y": mm_y,
                        "ImageIndex": 1,
                        "ImagesCount": 10,
                    },
                    "Ones": {
                        "X": BIG_X1,
                        "Y": mm_y,
                        "ImageIndex": 1,
                        "ImagesCount": 10,
                    },
                },
            },
            "Date": {
                "MonthAndDayAndYear": {
                    "OneLine": {
                        "Number": {
                            "TopLeftX": 5,
                            "TopLeftY": 192,
                            "BottomRightX": 121,
                            "BottomRightY": 220,
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
            "Activity": {
                "Steps": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": 222,
                        "BottomRightX": 121,
                        "BottomRightY": 250,
                        "Alignment": "Center",
                        "SpacingX": 1,
                        "SpacingY": 0,
                        "ImageIndex": 22,
                        "ImagesCount": 10,
                    }
                }
            },
            "Battery": {
                "BatteryText": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": 252,
                        "BottomRightX": 121,
                        "BottomRightY": 280,
                        "Alignment": "Center",
                        "SpacingX": 1,
                        "SpacingY": 0,
                        "ImageIndex": 32,
                        "ImagesCount": 10,
                    },
                    "SuffixImageIndex": 42,
                }
            },
        }
    else:
        hh_y, mm_y = 44, 128  # block 164 + secondary
        sy0, sy1 = 220, 250
        js_time = {
            "Hours": {
                "Tens": {"X": BIG_X0, "Y": hh_y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BIG_X1, "Y": hh_y, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": BIG_X0, "Y": mm_y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BIG_X1, "Y": mm_y, "ImageIndex": 1, "ImagesCount": 10},
            },
        }
        num = {
            "TopLeftX": 5,
            "TopLeftY": sy0,
            "BottomRightX": 121,
            "BottomRightY": sy1,
            "Alignment": "Center",
            "SpacingX": 1,
            "SpacingY": 0,
            "ImageIndex": 11,
            "ImagesCount": 10,
        }
        js = {
            "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
            "Time": js_time,
        }
        if secondary == "date":
            js["Date"] = {
                "MonthAndDayAndYear": {
                    "OneLine": {"Number": num, "DelimiterImageIndex": 21},
                    "TwoDigitsMonth": True,
                    "TwoDigitsDay": True,
                }
            }
        elif secondary == "steps":
            js["Activity"] = {"Steps": {"Number": num}}
        elif secondary == "pulse":
            js["Activity"] = {"Pulse": {"Number": num}}
        elif secondary in ("battery", "battery-bar"):
            js["Battery"] = {"BatteryText": {"Number": num, "SuffixImageIndex": 21}}
            if secondary == "battery-bar":
                # thin 10-seg bar under number
                for i in range(10):
                    block(10, 4, scol).save(out / f"{22 + i}.png")
                segs = [{"X": 13 + i * 10, "Y": 256} for i in range(10)]
                js["Battery"]["Linear"] = {"StartImageIndex": 22, "Segments": segs}
                # shift number up a bit to fit bar: adjust in place
                js["Battery"]["BatteryText"]["Number"]["TopLeftY"] = 216
                js["Battery"]["BatteryText"]["Number"]["BottomRightY"] = 244
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(
        name,
        len(list(out.glob("*.png"))),
        f"HH{hh_y} MM{mm_y if 'mm_y' in locals() else '-'}",
    )


build("clean-night-01-time", FG, FG, None)
build("clean-night-02-date", FG, FG, "date")
build("clean-night-03-steps", FG, FG, "steps")
build("clean-night-04-battery", FG, FG, "battery-bar")
build("clean-night-05-pulse", FG, FG, "pulse")
build("clean-night-06-trio", FG, FG, "trio")
