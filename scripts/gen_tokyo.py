#!/usr/bin/env python3
"""Tokyo Night/Day faces with Departure Mono for Mi Band 5."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
W, H = 126, 294
DEP = "/home/karoly/projects/Physiquinator/Physiquinator.UI/wwwroot/fonts/DepartureMono-Regular.woff2"

TN = {
    "bg": "#24283b",
    "fg": "#c0caf5",
    "dim": "#565f89",
    "blue": "#7aa2f7",
    "green": "#9ece6a",
    "cyan": "#7dcfff",
    "red": "#f7768e",
    "yellow": "#e0af68",
}
TD = {
    "bg": "#e1e2e7",
    "fg": "#3760bf",
    "dim": "#848cb5",
    "blue": "#2e7de9",
    "green": "#587539",
    "cyan": "#007197",
    "red": "#f52a65",
    "yellow": "#8c6c3e",
}


def glyph(ch, w, h, size, color, bg=None):
    bgc = bg if bg else (0, 0, 0, 0)
    img = Image.new("RGBA", (w, h), bgc)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(DEP, size)
    bbox = d.textbbox((0, 0), ch, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1]), ch, font=f, fill=color)
    return img


def build(name, P):
    out = ROOT / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    # 0 bg
    Image.new("RGB", (W, H), P["bg"]).save(out / "0.png")
    # 1-10 big time digits fg 34x56
    for i in range(10):
        glyph(str(i), 34, 56, 44, P["fg"]).save(out / f"{i + 1}.png")
    # 11 colon dim
    glyph(":", 16, 56, 40, P["dim"]).save(out / "11.png")
    # 12-21 date digits blue 18x28
    for i in range(10):
        glyph(str(i), 18, 28, 24, P["blue"]).save(out / f"{i + 12}.png")
    glyph("/", 18, 28, 24, P["dim"]).save(out / "22.png")
    # 23-32 steps digits green
    for i in range(10):
        glyph(str(i), 18, 28, 24, P["green"]).save(out / f"{i + 23}.png")
    # 33-42 battery digits cyan
    for i in range(10):
        glyph(str(i), 18, 28, 24, P["cyan"]).save(out / f"{i + 33}.png")
    glyph("%", 22, 28, 20, P["cyan"]).save(out / "43.png")
    # 44-53 pulse digits red
    for i in range(10):
        glyph(str(i), 18, 28, 24, P["red"]).save(out / f"{i + 44}.png")

    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": 26, "Y": 48, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 62, "Y": 48, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": 26, "Y": 108, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 62, "Y": 108, "ImageIndex": 1, "ImagesCount": 10},
            },
        },
        "Date": {
            "MonthAndDayAndYear": {
                "OneLine": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": 172,
                        "BottomRightX": 121,
                        "BottomRightY": 200,
                        "Alignment": "Center",
                        "SpacingX": 1,
                        "SpacingY": 0,
                        "ImageIndex": 12,
                        "ImagesCount": 10,
                    },
                    "DelimiterImageIndex": 22,
                },
                "TwoDigitsMonth": True,
                "TwoDigitsDay": True,
            }
        },
        "Activity": {
            "Steps": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 204,
                    "BottomRightX": 121,
                    "BottomRightY": 232,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 23,
                    "ImagesCount": 10,
                }
            },
            "Pulse": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 258,
                    "BottomRightX": 121,
                    "BottomRightY": 286,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 44,
                    "ImagesCount": 10,
                }
            },
        },
        "Battery": {
            "BatteryText": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 231,
                    "BottomRightX": 121,
                    "BottomRightY": 259,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 33,
                    "ImagesCount": 10,
                },
                "SuffixImageIndex": 43,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, "done", len(list(out.glob("*.png"))), "pngs")


build("tokyo-night", TN)
build("tokyo-day", TD)
