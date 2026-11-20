#!/usr/bin/env python3
"""Retro game faces, big stacked HH/MM, creative bars/icons."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
W, H = 126, 294
DEP = "/home/karoly/projects/Physiquinator/Physiquinator.UI/wwwroot/fonts/DepartureMono-Regular.woff2"


def F(size):
    return ImageFont.truetype(DEP, size)


def glyph(ch, w, h, size, color):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = F(size)
    bbox = d.textbbox((0, 0), ch, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1]), ch, font=f, fill=color)
    return img


def block(w, h, color, border=None):
    img = Image.new("RGBA", (w, h), color)
    if border:
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=border, width=1)
    return img


def bake_bg(base_color, border_color, labels):
    """labels: list of (text, x, y, size, color)"""
    bg = Image.new("RGB", (W, H), base_color)
    d = ImageDraw.Draw(bg)
    # border
    d.rectangle([0, 0, W - 1, H - 1], outline=border_color, width=3)
    # corner pixels (retro)
    for cx, cy in [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)]:
        d.rectangle(
            [
                cx - 4 if cx > 0 else cx,
                cy - 4 if cy > 0 else cy,
                cx + 4 if cx == 0 else cx,
                cy + 4 if cy == 0 else cy,
            ],
            fill=border_color,
        )
    for text, x, y, size, color in labels:
        f = F(size)
        # centered if x is None
        if x is None:
            bbox = d.textbbox((0, 0), text, font=f)
            x = (W - (bbox[2] - bbox[0])) // 2
        d.text((x, y), text, font=f, fill=color)
    # scanline dots faint
    for yy in range(8, H - 4, 6):
        for xx in range(6, W - 6, 6):
            px = bg.getpixel((xx, yy))
            bg.putpixel((xx, yy), tuple(max(0, c - 8) for c in px))
    return bg


def save_rgba(path, img):
    # flatten semi? keep RGBA, wfjs handles alpha via PNG
    img.save(path)


# ---------- 1. arcade-night ----------
def build_arcade():
    name = "retro-arcade-night"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    P = {
        "bg": "#1a1b26",
        "border": "#7dcfff",
        "fg": "#ffffff",
        "blue": "#7aa2f7",
        "green": "#9ece6a",
        "cyan": "#7dcfff",
        "red": "#f7768e",
        "dim": "#565f89",
    }
    bg = bake_bg(
        P["bg"],
        P["border"],
        [
            ("TIME", None, 6, 11, P["dim"]),
            ("STAGE", None, 168, 11, P["dim"]),
            ("SCORE", None, 198, 11, P["dim"]),
            ("HP", 10, 240, 11, P["cyan"]),
        ],
    )
    bg.save(out / "0.png")
    for i in range(10):
        save_rgba(out / f"{i + 1}.png", glyph(str(i), 46, 66, 56, P["fg"]))
    for i in range(10):  # 11-20 date blue 18x26
        save_rgba(out / f"{i + 11}.png", glyph(str(i), 18, 26, 22, P["blue"]))
    save_rgba(out / "21.png", glyph("/", 18, 26, 22, P["dim"]))
    for i in range(10):  # 22-31 steps green
        save_rgba(out / f"{i + 22}.png", glyph(str(i), 18, 26, 22, P["green"]))
    for i in range(10):  # 32-41 pulse red
        save_rgba(out / f"{i + 32}.png", glyph(str(i), 18, 26, 22, P["red"]))
    # step blocks 42-51 green 10x8, battery HP blocks 52-59 cyan 11x10
    for i in range(10):
        save_rgba(out / f"{i + 42}.png", block(10, 8, P["green"]))
    for i in range(8):
        save_rgba(out / f"{i + 52}.png", block(11, 10, P["cyan"], border="#1a1b26"))
    segs_steps = [{"X": 8 + i * 11, "Y": 232} for i in range(10)]
    segs_hp = [{"X": 32 + i * 12, "Y": 242} for i in range(8)]
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": 17, "Y": 24, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 24, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": 17, "Y": 94, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 94, "ImageIndex": 1, "ImagesCount": 10},
            },
        },
        "Date": {
            "MonthAndDayAndYear": {
                "OneLine": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": 180,
                        "BottomRightX": 121,
                        "BottomRightY": 206,
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
                    "TopLeftY": 210,
                    "BottomRightX": 121,
                    "BottomRightY": 230,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 22,
                    "ImagesCount": 10,
                }
            },
            "Pulse": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 256,
                    "BottomRightX": 121,
                    "BottomRightY": 282,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 32,
                    "ImagesCount": 10,
                }
            },
        },
        "StepsProgress": {"Linear": {"StartImageIndex": 42, "Segments": segs_steps}},
        "Battery": {"Linear": {"StartImageIndex": 52, "Segments": segs_hp}},
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


# ---------- 2. boss-day ----------
def build_boss():
    name = "retro-boss-day"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    P = {
        "bg": "#e1e2e7",
        "border": "#3760bf",
        "fg": "#1a1b26",
        "blue": "#2e7de9",
        "green": "#587539",
        "red": "#f52a65",
        "dim": "#848cb5",
    }
    bg = bake_bg(
        P["bg"],
        P["border"],
        [
            ("BOSS", None, 6, 11, P["red"]),
            ("TIME", None, 22, 10, P["dim"]),
            ("HP-STEPS", None, 172, 10, P["dim"]),
            ("BAT%", None, 236, 10, P["dim"]),
        ],
    )
    bg.save(out / "0.png")
    for i in range(10):
        save_rgba(out / f"{i + 1}.png", glyph(str(i), 46, 66, 56, P["fg"]))
    for i in range(10):
        save_rgba(out / f"{i + 11}.png", glyph(str(i), 18, 26, 22, P["blue"]))
    save_rgba(out / "21.png", glyph("/", 18, 26, 22, P["dim"]))
    for i in range(10):  # battery red numbers
        save_rgba(out / f"{i + 22}.png", glyph(str(i), 20, 28, 24, P["red"]))
    save_rgba(out / "32.png", glyph("%", 20, 28, 20, P["red"]))
    # steps HP bar: 12 blocks green 9x12 with dark border
    for i in range(12):
        save_rgba(out / f"{i + 33}.png", block(9, 12, P["green"], border="#1a1b26"))
    segs = [{"X": 9 + i * 9, "Y": 186} for i in range(12)]
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": 17, "Y": 34, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 34, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": 17, "Y": 102, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 102, "ImageIndex": 1, "ImagesCount": 10},
            },
        },
        "Date": {
            "MonthAndDayAndYear": {
                "OneLine": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": 204,
                        "BottomRightX": 121,
                        "BottomRightY": 230,
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
        "StepsProgress": {"Linear": {"StartImageIndex": 33, "Segments": segs}},
        "Battery": {
            "BatteryText": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 248,
                    "BottomRightX": 121,
                    "BottomRightY": 276,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 22,
                    "ImagesCount": 10,
                },
                "SuffixImageIndex": 32,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


# ---------- 3. invader-big : max visibility ----------
def build_invader():
    name = "retro-invader-big"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    VOLT = "#FAFF00"
    bg = bake_bg(
        "#000000",
        VOLT,
        [
            ("1UP", None, 6, 11, VOLT),
            ("BAT", None, 248, 11, "#8a90b8"),
        ],
    )
    bg.save(out / "0.png")
    for i in range(
        10
    ):  # huge 54x78, HH volt, reuse for MM white? keep volt for both for max brightness
        save_rgba(out / f"{i + 1}.png", glyph(str(i), 54, 78, 64, VOLT))
    # battery bar blocks white 11x12
    for i in range(10):
        save_rgba(out / f"{i + 11}.png", block(11, 12, "#ffffff", border="#000000"))
    segs = [{"X": 8 + i * 11, "Y": 262} for i in range(10)]
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": 9, "Y": 24, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 24, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": 9, "Y": 108, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 108, "ImageIndex": 1, "ImagesCount": 10},
            },
        },
        "Battery": {"Linear": {"StartImageIndex": 11, "Segments": segs}},
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


# ---------- 4. dungeon-icons : battery as 5 pixel batteries, steps as number ----------
def build_dungeon():
    name = "retro-dungeon-icons"
    out = ROOT / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    P = {
        "bg": "#24283b",
        "border": "#9ece6a",
        "fg": "#c0caf5",
        "gold": "#e0af68",
        "red": "#f7768e",
    }
    bg = bake_bg(
        P["bg"],
        P["border"],
        [
            ("QUEST", None, 6, 11, P["gold"]),
            ("GOLD=STEPS", None, 196, 10, P["gold"]),
            ("LIFE", None, 226, 10, P["red"]),
        ],
    )
    bg.save(out / "0.png")
    for i in range(10):
        save_rgba(out / f"{i + 1}.png", glyph(str(i), 42, 62, 52, P["fg"]))
    for i in range(10):  # steps gold
        save_rgba(out / f"{i + 11}.png", glyph(str(i), 18, 26, 22, P["gold"]))
    # 5 battery icons 34x16: pixel battery with fill levels
    for lvl in range(5):
        img = Image.new("RGBA", (34, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 2, 29, 13], outline=P["red"], width=2)
        d.rectangle([30, 5, 33, 10], fill=P["red"])
        fill_w = int(26 * lvl / 4)
        if fill_w > 0:
            d.rectangle([2, 4, 2 + fill_w, 11], fill=P["red"])
        save_rgba(out / f"{21 + lvl}.png", img)
    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": 21, "Y": 30, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 30, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": 21, "Y": 96, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": 63, "Y": 96, "ImageIndex": 1, "ImagesCount": 10},
            },
        },
        "Activity": {
            "Steps": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 208,
                    "BottomRightX": 121,
                    "BottomRightY": 234,
                    "Alignment": "Center",
                    "SpacingX": 1,
                    "SpacingY": 0,
                    "ImageIndex": 11,
                    "ImagesCount": 10,
                }
            }
        },
        "Battery": {
            "BatteryIcon": {"X": 46, "Y": 240, "ImageIndex": 21, "ImagesCount": 5}
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    print(name, len(list(out.glob("*.png"))))


build_arcade()
build_boss()
build_invader()
build_dungeon()
