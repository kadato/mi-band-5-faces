#!/usr/bin/env python3
"""Max-time variants: tight HH/MM, weekday top, date below time, steps bottom."""

from PIL import Image, ImageDraw, ImageFont, ImageColor
from pathlib import Path
import json
import subprocess
import shutil

ROOT = Path(__file__).resolve().parent.parent
W, H = 126, 294
DEP = str(ROOT / "fonts" / "DepartureMono-Regular.woff2")
BG = "#24283b"
DIM = "#565f89"
RED = "#f7768e"
ORANGE = "#ff9e64"


def F(s):
    return ImageFont.truetype(DEP, s)


def glyph(ch, w, h, size, color, thresh=100):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = F(size)
    bb = d.textbbox((0, 0), ch, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = int((w - tw) / 2 - bb[0])
    ty = int((h - th) / 2 - bb[1])
    d.text((tx, ty), ch, font=f, fill=color)
    r, g, b, a = img.split()
    # Binarize alpha to {0, 255} with threshold 100 so all strokes (including top loops/bars) survive
    a = a.point(lambda p: 255 if p >= thresh else 0)
    return Image.merge("RGBA", (r, g, b, a))


def make_battery_icon(level):
    w, h, border = 44, 22, 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Low-only indicator: hidden when battery is normal/full (>= 20%, level >= 2)
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
    r, g, b, a = img.split()
    a = a.point(lambda p: 255 if p >= 128 else 0)
    return Image.merge("RGBA", (r, g, b, a))


# Non-overlapping geometry for Mi Band 5 hardware display engine (Balanced layout)
BW, BH = 44, 65
H_GAP = 4
BX0 = (W - (2 * BW + H_GAP)) // 2  # 17
BX1 = BX0 + BW + H_GAP  # 65
WD_Y = 12  # weekday 44x20 (Y: 12..32)
DATE_Y0, DATE_Y1 = 36, 60  # date (Y: 36..60)
HH_Y = 72  # Hours 44x65 (Y: 72..137)
MM_Y = 150  # Minutes 44x65 (Y: 150..215)
BATT_W, BATT_H = 44, 22
BATT_X = (W - BATT_W) // 2  # 41
BATT_Y = 224  # battery warning badge (Y: 224..246, between Minutes and Steps)
STEP_W, STEP_H = 22, 28
STEPS_Y0, STEPS_Y1 = 252, 280  # steps 22x28 (Y: 252..280, bottom margin 14px)


def generate_preview_and_pack(name, preview_idx=55):
    out = ROOT / "faces" / name
    js_file = out / "watchface.json"
    js = json.loads(js_file.read_text())

    im_bg = Image.open(out / "0.png").convert("RGBA")

    # 1. Weekday FRI (Image 52 = 48 + 4)
    im_fri = Image.open(out / "52.png")
    im_bg.paste(im_fri, (41, WD_Y), im_fri)

    # 2. Date 11/20 (21..30 digits, 31 slash)
    im_d1 = Image.open(out / "22.png")
    im_slash = Image.open(out / "31.png")
    im_d2 = Image.open(out / "23.png")
    im_d0 = Image.open(out / "21.png")
    dw = im_d1.width * 4 + im_slash.width + 4
    dx = (W - dw) // 2
    im_bg.paste(im_d1, (dx, DATE_Y0), im_d1)
    dx += im_d1.width + 1
    im_bg.paste(im_d1, (dx, DATE_Y0), im_d1)
    dx += im_d1.width + 1
    im_bg.paste(im_slash, (dx, DATE_Y0), im_slash)
    dx += im_slash.width + 1
    im_bg.paste(im_d2, (dx, DATE_Y0), im_d2)
    dx += im_d2.width + 1
    im_bg.paste(im_d0, (dx, DATE_Y0), im_d0)

    # 3. Time 10:09 (Hours 1..10, Minutes 11..20)
    im_h1 = Image.open(out / "2.png")
    im_h0 = Image.open(out / "1.png")
    im_bg.paste(im_h1, (BX0, HH_Y), im_h1)
    im_bg.paste(im_h0, (BX1, HH_Y), im_h0)

    im_m0 = Image.open(out / "11.png")
    im_m9 = Image.open(out / "20.png")
    im_bg.paste(im_m0, (BX0, MM_Y), im_m0)
    im_bg.paste(im_m9, (BX1, MM_Y), im_m9)

    # 4. Steps 8432 (32..41 digits)
    im_s8 = Image.open(out / "40.png")
    im_s4 = Image.open(out / "36.png")
    im_s3 = Image.open(out / "35.png")
    im_s2 = Image.open(out / "34.png")
    sw = im_s8.width + im_s4.width + im_s3.width + im_s2.width + 3
    sx = (W - sw) // 2
    im_bg.paste(im_s8, (sx, STEPS_Y0), im_s8)
    sx += im_s8.width + 1
    im_bg.paste(im_s4, (sx, STEPS_Y0), im_s4)
    sx += im_s4.width + 1
    im_bg.paste(im_s3, (sx, STEPS_Y0), im_s3)
    sx += im_s3.width + 1
    im_bg.paste(im_s2, (sx, STEPS_Y0), im_s2)

    # 5. Battery: level 2 transparent (normal battery state, exact match with watch)
    im_batt = Image.open(out / "44.png")
    im_bg.paste(im_batt, (BATT_X, BATT_Y), im_batt)

    # Save preview image as RGB
    im_bg.convert("RGB").save(out / f"{preview_idx}.png")

    # Add PreviewEN/CN/CN2 to Background
    js["Background"]["PreviewEN"] = {"X": 0, "Y": 0, "ImageIndex": preview_idx}
    js["Background"]["PreviewCN"] = {"X": 0, "Y": 0, "ImageIndex": preview_idx}
    js["Background"]["PreviewCN2"] = {"X": 0, "Y": 0, "ImageIndex": preview_idx}
    js_file.write_text(json.dumps(js, indent=2))

    # Compile with wfjs
    bin_dir = ROOT / "bin"
    bin_dir.mkdir(exist_ok=True)
    target_bin = bin_dir / f"{name}.bin"
    packed_file = ROOT / f"{name}_packed.bin"
    if packed_file.exists():
        packed_file.unlink()

    r = subprocess.run(
        ["./node_modules/.bin/wfjs", "writeBin", "-i", f"faces/{name}", "-m", "miband5"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Failed to build {name}.bin: {r.stderr}")
    if packed_file.exists():
        packed_file.replace(target_bin)
    print(f"Packaged {target_bin} ({target_bin.stat().st_size} bytes)")

    # Verify hardware safety: parse the packed binary
    verify_script = f"""
const fs = require('fs');
const {{ getAvailableModels, parseWatchFaceBin }} = require('./node_modules/watchface-js/dist/watchFaceBinTools/watchFaceBinParser.js');
const mb5 = getAvailableModels().find(m => m.id === 'miband5');
const buf = fs.readFileSync('{target_bin}');
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const wf = parseWatchFaceBin(ab, mb5.fileType);

// Verify mandatory firmware tags
if (wf.parameters.Time.DrawingOrder !== false) {{
  throw new Error('Time.DrawingOrder must be false (Protobuf tag 11)');
}}
if (wf.parameters.Activity.UnknownV7 !== 0) {{
  throw new Error('Activity.UnknownV7 must be 0 (Protobuf tag 7)');
}}
if (wf.parameters.Time.Hours.Tens.ImageIndex === wf.parameters.Time.Minutes.Tens.ImageIndex) {{
  throw new Error('Hours and Minutes must have distinct ImageIndex sets');
}}

for (let i = 0; i < wf.images.length; i++) {{
  const img = wf.images[i];
  if (i !== 0 && i !== {preview_idx}) {{
    if (img.pixelFormat !== 0x64) {{
      throw new Error(`Image ${{i}} has format 0x${{img.pixelFormat.toString(16)}} (expected 0x64 8bpp indexed colors)`);
    }}
    const bSize = 16 + 1024 + img.width * img.height;
    if (bSize > 4096) {{
      throw new Error(`Image ${{i}} (${{img.width}}x${{img.height}}) binary size ${{bSize}}B exceeds 4KB hardware buffer`);
    }}
  }}
}}
console.log('All {name} images verified hardware-safe (0x64 indexed, <= 4096 bytes)');
"""
    v = subprocess.run(
        ["node", "-e", verify_script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if v.returncode != 0:
        raise RuntimeError(
            f"Hardware safety verification failed for {name}: {v.stderr}"
        )
    print(v.stdout.strip())

    # Copy to Windows Downloads if accessible
    win_dl = Path("/mnt/c/Users/Karoly/Downloads")
    if win_dl.exists():
        shutil.copy2(target_bin, win_dl / f"{name}.bin")
        print(f"Copied {name}.bin to {win_dl}")


def build(name, tcol, wdcol, datecol, stepcol):
    out = ROOT / "faces" / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()

    # 0.png: background
    Image.new("RGB", (W, H), BG).save(out / "0.png")

    # 1..10.png: Hours digits 0..9 (ImageIndex: 1)
    for i in range(10):
        glyph(str(i), BW, BH, 80, tcol).save(out / f"{i + 1}.png")

    # 11..20.png: Minutes digits 0..9 (ImageIndex: 11) - separate images!
    for i in range(10):
        glyph(str(i), BW, BH, 80, tcol).save(out / f"{i + 11}.png")

    # 21..30.png: Date digits 0..9 (ImageIndex: 21)
    for i in range(10):
        glyph(str(i), 18, 24, 22, datecol).save(out / f"{i + 21}.png")

    # 31.png: Date slash (DelimiterImageIndex: 31)
    glyph("/", 18, 24, 22, DIM).save(out / "31.png")

    # 32..41.png: Steps digits 0..9 (ImageIndex: 32)
    for i in range(10):
        glyph(str(i), STEP_W, STEP_H, 28, stepcol, thresh=100).save(out / f"{i + 32}.png")

    # 42..47.png: Battery icon levels 0..5 (ImageIndex: 42)
    for idx in range(6):
        make_battery_icon(idx).save(out / f"{42 + idx}.png")

    # 48..54.png: Weekdays MON..SUN (ImageIndex: 48)
    for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
        glyph(dd, 44, 20, 18, wdcol).save(out / f"{48 + i}.png")

    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": BX0, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": BX0, "Y": MM_Y, "ImageIndex": 11, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": MM_Y, "ImageIndex": 11, "ImagesCount": 10},
            },
            "DrawingOrder": False,
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
                    "ImageIndex": 32,
                    "ImagesCount": 10,
                }
            },
            "UnknownV7": 0,
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
                        "ImageIndex": 21,
                        "ImagesCount": 10,
                    },
                    "DelimiterImageIndex": 31,
                },
                "TwoDigitsMonth": True,
                "TwoDigitsDay": True,
            },
            "ENWeekDays": {"X": 41, "Y": WD_Y, "ImageIndex": 48, "ImagesCount": 7},
        },
        "Battery": {
            "BatteryIcon": {
                "X": BATT_X,
                "Y": BATT_Y,
                "ImageIndex": 42,
                "ImagesCount": 6,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    generate_preview_and_pack(name, preview_idx=55)
    print(name, len(list(out.glob("*.png"))))


def build_duo(name, hhcol, mmcol, wdcol, datecol, stepcol):
    out = ROOT / "faces" / name
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()

    # 0.png: background
    Image.new("RGB", (W, H), BG).save(out / "0.png")

    # 1..10.png: Hours digits 0..9 (ImageIndex: 1)
    for i in range(10):
        glyph(str(i), BW, BH, 80, hhcol).save(out / f"{i + 1}.png")

    # 11..20.png: Minutes digits 0..9 (ImageIndex: 11) - separate mmcol!
    for i in range(10):
        glyph(str(i), BW, BH, 80, mmcol).save(out / f"{i + 11}.png")

    # 21..30.png: Date digits 0..9 (ImageIndex: 21)
    for i in range(10):
        glyph(str(i), 18, 24, 22, datecol).save(out / f"{i + 21}.png")

    # 31.png: Date slash (DelimiterImageIndex: 31)
    glyph("/", 18, 24, 22, DIM).save(out / "31.png")

    # 32..41.png: Steps digits 0..9 (ImageIndex: 32)
    for i in range(10):
        glyph(str(i), STEP_W, STEP_H, 28, stepcol, thresh=100).save(out / f"{i + 32}.png")

    # 42..47.png: Battery icon levels 0..5 (ImageIndex: 42)
    for idx in range(6):
        make_battery_icon(idx).save(out / f"{42 + idx}.png")

    # 48..54.png: Weekdays MON..SUN (ImageIndex: 48)
    for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
        glyph(dd, 44, 20, 18, wdcol).save(out / f"{48 + i}.png")

    js = {
        "Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}},
        "Time": {
            "Hours": {
                "Tens": {"X": BX0, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": HH_Y, "ImageIndex": 1, "ImagesCount": 10},
            },
            "Minutes": {
                "Tens": {"X": BX0, "Y": MM_Y, "ImageIndex": 11, "ImagesCount": 10},
                "Ones": {"X": BX1, "Y": MM_Y, "ImageIndex": 11, "ImagesCount": 10},
            },
            "DrawingOrder": False,
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
                    "ImageIndex": 32,
                    "ImagesCount": 10,
                }
            },
            "UnknownV7": 0,
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
                        "ImageIndex": 21,
                        "ImagesCount": 10,
                    },
                    "DelimiterImageIndex": 31,
                },
                "TwoDigitsMonth": True,
                "TwoDigitsDay": True,
            },
            "ENWeekDays": {"X": 41, "Y": WD_Y, "ImageIndex": 48, "ImagesCount": 7},
        },
        "Battery": {
            "BatteryIcon": {
                "X": BATT_X,
                "Y": BATT_Y,
                "ImageIndex": 42,
                "ImagesCount": 6,
            }
        },
    }
    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    generate_preview_and_pack(name, preview_idx=55)
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

# Regenerate faces.js
subprocess.run(["python3", str(ROOT / "scripts" / "gen_exact.py")], check=True)
