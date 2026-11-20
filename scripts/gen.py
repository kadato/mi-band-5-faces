#!/usr/bin/env python3
"""Generate Mi Band 5 watchface assets: flashlight + daily."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
W, H = 126, 294
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def text_img(char, w, h, font_size, fg=(255, 255, 255, 255), bg=(0, 0, 0, 0)):
    img = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(FONT_BOLD, font_size)
    except:
        f = ImageFont.load_default()
    # center text
    bbox = d.textbbox((0, 0), char, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1]), char, font=f, fill=fg)
    return img


# ---------- FLASHLIGHT ----------
fl = ROOT / "flashlight"
fl.mkdir(parents=True, exist_ok=True)
# background full white
Image.new("RGB", (W, H), (255, 255, 255)).save(fl / "0.png")
# digits 1-10 : full white blocks 34x54 (invisible time, keeps screen 100% white)
for i in range(10):
    Image.new("RGB", (34, 54), (255, 255, 255)).save(fl / f"{i + 1}.png")

fl_json = {
    "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
    "Time": {
        "Hours": {
            "Tens": {"X": 29, "Y": 120, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": 63, "Y": 120, "ImageIndex": 1, "ImagesCount": 10},
        },
        "Minutes": {
            "Tens": {"X": 29, "Y": 120, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": 63, "Y": 120, "ImageIndex": 1, "ImagesCount": 10},
        },
    },
}
(fl / "watchface.json").write_text(json.dumps(fl_json, indent=2))
print(f"flashlight: {len(list(fl.glob('*.png')))} pngs")

# ---------- DAILY ----------
dy = ROOT / "daily"
dy.mkdir(parents=True, exist_ok=True)
# 0: black background
Image.new("RGB", (W, H), (0, 0, 0)).save(dy / "0.png")
# 1-10: big white digits 0-9, 34x54 transparent
for d in range(10):
    text_img(str(d), 34, 54, 48).save(dy / f"{d + 1}.png")
# 11 is index 11 -> file 11.png : colon, 16x54
text_img(":", 16, 54, 44).save(dy / "11.png")
# 12-21: small digits 0-9, 18x28 transparent
for d in range(10):
    text_img(str(d), 18, 28, 26).save(dy / f"{d + 12}.png")
# 22: slash
text_img("/", 18, 28, 26).save(dy / "22.png")
# 23: percent
text_img("%", 22, 28, 22).save(dy / "23.png")
# 24: BT icon? simple small dot / bluetooth placeholder - use "o" for status? Actually Status needs On/Off images, skip status for now.

daily_json = {
    "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
    "Time": {
        "Hours": {
            "Tens": {"X": 26, "Y": 55, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": 62, "Y": 55, "ImageIndex": 1, "ImagesCount": 10},
        },
        "Minutes": {
            "Tens": {"X": 26, "Y": 115, "ImageIndex": 1, "ImagesCount": 10},
            "Ones": {"X": 62, "Y": 115, "ImageIndex": 1, "ImagesCount": 10},
        },
        "DelimiterImage": {"X": 59, "Y": 100, "ImageIndex": 11},
    },
    "Date": {
        "MonthAndDayAndYear": {
            "OneLine": {
                "Number": {
                    "TopLeftX": 5,
                    "TopLeftY": 180,
                    "BottomRightX": 121,
                    "BottomRightY": 208,
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
                "TopLeftY": 212,
                "BottomRightX": 121,
                "BottomRightY": 240,
                "Alignment": "Center",
                "SpacingX": 1,
                "SpacingY": 0,
                "ImageIndex": 12,
                "ImagesCount": 10,
            }
        }
    },
    "Battery": {
        "BatteryText": {
            "Number": {
                "TopLeftX": 5,
                "TopLeftY": 244,
                "BottomRightX": 121,
                "BottomRightY": 270,
                "Alignment": "Center",
                "SpacingX": 1,
                "SpacingY": 0,
                "ImageIndex": 12,
                "ImagesCount": 10,
            },
            "SuffixImageIndex": 23,
        }
    },
}
(dy / "watchface.json").write_text(json.dumps(daily_json, indent=2))
print(f"daily: {len(list(dy.glob('*.png')))} pngs")
print("done")
