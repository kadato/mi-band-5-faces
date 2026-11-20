#!/usr/bin/env python3
"""Build clean-night-18-custom face from custom-design.json.

Single source of truth: this script generates the PNGs + watchface.json.
preview.html draws those same PNGs, so preview == .bin pixels.
Pack with: wfjs writeBin -i clean-night-18-custom -m miband5

Supports every element the designer exposes: time (stack/side, SS,
delimiter), date + weekdays, steps, distance, calories, pulse, PAI,
temperature, hi/lo, humidity, wind, UV, alarm, battery text, low-only
battery icon, BT/lock/DND status, goal bar.
"""

import json
import sys
import subprocess
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageColor

ROOT = Path(__file__).resolve().parent
DESIGN = ROOT / "custom-design.json"

FONTS = {
    "Departure Mono": ROOT / "fonts" / "DepartureMono-Regular.woff2",
    "JetBrains Mono": ROOT / "fonts" / "jetbrains-mono-5.woff2",
    "ui-monospace, monospace": Path(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    ),
    "system-ui, sans-serif": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
}
FALLBACK = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")

W, H = 126, 294
DIM = "#565f89"
RED = "#f7768e"
ORANGE = "#ff9e64"
GAP = 3


def font_for(name, size):
    p = FONTS.get(name, FALLBACK)
    if not p.exists():
        p = FALLBACK
    return ImageFont.truetype(str(p), size)


def glyph(ch, w, h, size, color, fname, thresh=100):
    tmp = Image.new("RGBA", (w + 100, h + 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    f = font_for(fname, size)
    d.text((50, 50), ch, font=f, fill=color)
    ab = tmp.getbbox()
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if ab:
        cropped = tmp.crop(ab)
        ox = (w - cropped.width) // 2
        oy = (h - cropped.height) // 2
        img.paste(cropped, (ox, oy), cropped)
    r, g, b, a = img.split()
    # Binarize alpha to {0, 255} with threshold 100 so all strokes survive without clipping
    a = a.point(lambda p: 255 if p >= thresh else 0)
    return Image.merge("RGBA", (r, g, b, a))


def measure_digits(fname, size):
    f = font_for(fname, size)
    max_w, max_h = 0, 0
    for ch in "0123456789":
        tmp = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        d.text((50, 50), ch, font=f, fill=(255, 255, 255, 255))
        ab = tmp.getbbox()
        if ab:
            max_w = max(max_w, ab[2] - ab[0])
            max_h = max(max_h, ab[3] - ab[1])
    return max(max_w, 1), max(max_h, 1)


def text_img(s, size, color, fname, pad=2):
    f = font_for(fname, size)
    tmp = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bb[0], pad - bb[1]), s, font=f, fill=color)
    r, g, b, a = img.split()
    # Binarize alpha to {0, 255} for hardware safety
    a = a.point(lambda p: 255 if p >= 100 else 0)
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


def DEFAULT_DESIGN():
    g = lambda color, size, show=True, font="global", spacing=0: {
        "show": show,
        "color": color,
        "size": size,
        "font": font,
        "spacing": spacing,
    }
    return {
        "bg": "#24283b",
        "globalFont": "Departure Mono",
        "layout": "stack",
        "topOrder": "wd-dt",
        "delimiter": ":",
        "goalBar": False,
        "rowGap": 6,
        "y": {"top": 12, "time": 72, "low": 252, "batt": 224},
        "groups": {
            "hh": g("#c0caf5", 80, True, "global", 4),
            "mm": g("#c0caf5", 80, True, "global", 4),
            "ss": g("#565f89", 26, False, "global", 0),
            "wd": g("#7aa2f7", 18, True, "global", 2),
            "dt": g("#7aa2f7", 22, True, "global", 0),
            "st": g("#7aa2f7", 28, True, "global", 0),
            "di": g("#7aa2f7", 22, False, "global", 0),
            "ca": g("#7aa2f7", 22, False, "global", 0),
            "pu": g("#f7768e", 22, False, "global", 0),
            "pai": g("#e0af68", 22, False, "global", 0),
            "tmp": g("#7dcfff", 24, False, "global", 0),
            "hil": g("#7dcfff", 16, False, "global", 0),
            "hum": g("#7dcfff", 22, False, "global", 0),
            "wind": g("#7dcfff", 22, False, "global", 0),
            "uv": g("#7dcfff", 22, False, "global", 0),
            "al": g("#7aa2f7", 18, False, "global", 0),
            "bp": g("#7dcfff", 24, False, "global", 0),
            "sn": g("#7aa2f7", 18, False, "global", 4),
        },
        "values": {
            "hh": "12",
            "mm": "45",
            "ss": "30",
            "date": "11/17",
            "day": "WED",
            "steps": 8432,
            "goal": 10000,
            "strideCm": 75,
            "kcalPerStep": 0.04,
            "unit": "km",
            "pulse": "72",
            "pai": "86",
            "temp": "21",
            "hi": "24",
            "lo": "17",
            "hum": "55",
            "wind": "3",
            "uv": "3",
            "alarm": "07:00",
            "alarmOn": True,
            "bt": True,
            "lock": False,
            "dnd": False,
            "batt": 12,
        },
    }


def res_font(groups, gid, global_font):
    f = groups[gid].get("font") or "global"
    return global_font if f == "global" else f


def build(d):
    dd = DEFAULT_DESIGN()
    G = d["groups"]
    for gid, gd in dd["groups"].items():
        G[gid] = {**gd, **G.get(gid, {})}
    for k, v in dd["y"].items():
        d["y"].setdefault(k, v)
    gf = d.get("globalFont", "Departure Mono")
    bg = d["bg"]
    layout_mode = d.get("layout", "stack")
    top_order = d.get("topOrder", "wd-dt")
    delim = d.get("delimiter", ":")
    gap = int(d.get("rowGap", -25))
    y = d["y"]
    topY, timeY, lowY, battY = (
        int(y["top"]),
        int(y["time"]),
        int(y["low"]),
        int(y["batt"]),
    )

    out = ROOT / "faces" / "clean-night-18-custom"
    out.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()

    Image.new("RGB", (W, H), bg).save(out / "0.png")
    nxt = [1]
    files = {}

    def alloc(n=1):
        i = nxt[0]
        nxt[0] += n
        return i

    def save(img):
        i = alloc()
        img.save(out / f"{i}.png")
        return i

    def digit_set(color, size, fname, chars="0123456789", box=None):
        if box:
            bw, bh = box
        else:
            gw, gh = measure_digits(fname, size)
            bw, bh = gw + 4, gh + 4
        base = alloc(10)
        for k, ch in enumerate("0123456789"):
            glyph(ch, bw, bh, size, color, fname).save(out / f"{base + k}.png")
        return base, bw, bh

    def small_text(s, color, size, fname):
        img = text_img(s, size, color, fname)
        return save(img), img.width, img.height

    # ---- time digits (sizes auto-fit band width in side mode) ----
    hh, mm, ss = G["hh"], G["mm"], G["ss"]
    hhF = res_font(G, "hh", gf)
    mmF = res_font(G, "mm", gf)
    ssF = res_font(G, "ss", gf)
    linked = (
        mm["color"].lower() == hh["color"].lower()
        and mm.get("font", "global") == hh.get("font", "global")
        and int(mm["size"]) == int(hh["size"])
    )
    hhSize = int(hh["size"])
    gw, gh = measure_digits(hhF, hhSize)
    BW = gw + 6
    BH = gh + 5
    if BW % 2 != 0:
        BW += 1
    if BH % 2 != 0:
        BH += 1
    tfont = hhSize

    if linked:
        mmBase = None
        BW2, BH2, tfont2, mmF, mmSize = BW, BH, tfont, hhF, hhSize
    else:
        mmSize = int(mm["size"])
        gw2, gh2 = measure_digits(mmF, mmSize)
        BW2 = gw2 + 6
        BH2 = gh2 + 5
        if BW2 % 2 != 0:
            BW2 += 1
        if BH2 % 2 != 0:
            BH2 += 1
        tfont2 = mmSize

    if ss["show"]:
        ssSize = int(ss["size"])
        ssGW, ssGH = measure_digits(ssF, ssSize)
        ssBW = ssGW + 4
        ssBH = ssGH + 4
        if ssBW % 2 != 0:
            ssBW += 1
        if ssBH % 2 != 0:
            ssBH += 1
        ssTfont = ssSize
    else:
        ssBH = ssBW = ssTfont = 0

    if layout_mode == "side":
        _ci = text_img(delim, min(tfont, 36), hh["color"], hhF)
        _cw = _ci.width
        _sp = max(0, int(hh.get("spacing", 0)))
        _sp2 = max(0, int(mm.get("spacing", 0)))
        _tot = (2 * BW + _sp) + _cw + 6 + (2 * BW2 + _sp2)
        if ss["show"]:
            _tot += _cw + 6 + (2 * ssBW + max(0, int(ss.get("spacing", 0))))
        if _tot > 118:
            f = 118 / _tot
            hhSize = max(10, round(hhSize * f))
            mmSize = max(10, round(mmSize * f))
            gw, gh = measure_digits(hhF, hhSize)
            BW, BH = gw + 4, gh + 4
            gw2, gh2 = measure_digits(mmF, mmSize)
            BW2, BH2 = gw2 + 4, gh2 + 4
            tfont, tfont2 = hhSize, mmSize
            if ss["show"]:
                ssSize = max(8, round(ssSize * f))
                ssGW, ssGH = measure_digits(ssF, ssSize)
                ssBW, ssBH = ssGW + 2, ssGH + 2
                ssTfont = ssSize

    hhBase, _, _ = digit_set(hh["color"], tfont, hhF, box=(BW, BH))
    # Mi Band 5 firmware requires distinct ImageIndex sets for Hours and Minutes;
    # sharing hhBase causes the firmware display engine to fail initializing Time.
    mmBase, _, _ = digit_set(mm["color"], tfont2, mmF, box=(BW2, BH2))
    ssBase = None
    if ss["show"]:
        ssBase, _, _ = digit_set(ss["color"], ssTfont, ssF, box=(ssBW, ssBH))
    colonIdx = colonW = colonH = None
    if layout_mode == "side":
        colonIdx, colonW, colonH = small_text(delim, hh["color"], min(tfont, 36), hhF)

    sp = max(0, int(hh.get("spacing", 0)))
    step = BW + sp
    sp2 = max(0, int(mm.get("spacing", 0)))
    step2 = BW2 + sp2
    gap = max(0, int(d.get("rowGap", 6)))
    MM_Y = timeY + BH + gap

    if layout_mode == "stack":
        HH_X0 = 63 - (2 * BW + sp) // 2
        HH_X1 = HH_X0 + step
        MM_X0 = 63 - (2 * BW2 + sp2) // 2
        MM_X1 = MM_X0 + step2
        if ss["show"]:
            ssp = max(0, int(ss.get("spacing", 0)))
            sstep = ssBW + ssp
            SS_X0 = 63 - (2 * ssBW + ssp) // 2
            SS_X1 = SS_X0 + sstep
            SS_Y = MM_Y + BH2 + GAP
        else:
            SS_X0 = SS_X1 = HH_X0
            SS_Y = MM_Y + BH2
    else:
        # side: HH tens/ones, delim, MM tens/ones [, delim, SS tens/ones]
        parts = [2 * BW + sp, colonW + 6, 2 * BW2 + sp2]
        if ss["show"]:
            parts += [colonW + 6, 2 * ssBW + max(0, int(ss.get("spacing", 0)))]
        total = sum(parts)
        x = 63 - total // 2
        HH_X0, HH_X1 = x, x + step
        x += 2 * BW + sp
        dx = x + 3
        x += colonW + 6
        MM_X0, MM_X1 = x, x + step2
        x += 2 * BW2 + sp2
        SS_X0 = SS_X1 = None
        if ss["show"]:
            x += 3
            dx2 = x
            x += colonW + 6
            ssp = max(0, int(ss.get("spacing", 0)))
            sstep = ssBW + ssp
            SS_X0, SS_X1 = x, x + sstep
        else:
            dx2 = None
        MM_Y = timeY
        SS_Y = timeY

    time_js = {
        "Hours": {
            "Tens": {"X": HH_X0, "Y": timeY, "ImageIndex": hhBase, "ImagesCount": 10},
            "Ones": {"X": HH_X1, "Y": timeY, "ImageIndex": hhBase, "ImagesCount": 10},
        },
        "Minutes": {
            "Tens": {"X": MM_X0, "Y": MM_Y, "ImageIndex": mmBase, "ImagesCount": 10},
            "Ones": {"X": MM_X1, "Y": MM_Y, "ImageIndex": mmBase, "ImagesCount": 10},
        },
        "DrawingOrder": False,
    }
    if ss["show"]:
        time_js["Seconds"] = {
            "Tens": {"X": SS_X0, "Y": SS_Y, "ImageIndex": ssBase, "ImagesCount": 10},
            "Ones": {"X": SS_X1, "Y": SS_Y, "ImageIndex": ssBase, "ImagesCount": 10},
        }
    if layout_mode == "side":
        time_js["DelimiterImage"] = {"X": dx, "Y": timeY, "ImageIndex": colonIdx}

    # ---- top block: weekday + date ----
    wd, dt = G["wd"], G["dt"]
    wdF = res_font(G, "wd", gf)
    dtF = res_font(G, "dt", gf)
    cur = topY
    wd_js = dt_js = None
    wdH = dtH = 0
    order = ["wd", "dt"] if top_order == "wd-dt" else ["dt", "wd"]
    tops = {}
    for k in order:
        if k == "wd" and wd["show"]:
            wdH = round(wd["size"] * 1.1)
            wdW = round(wd["size"] * 0.8 * 3) + 1
            base = alloc(7)
            for i, dd in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
                glyph(dd, wdW, wdH, wd["size"], wd["color"], wdF).save(
                    out / f"{base + i}.png"
                )
            tops["wd"] = (base, 63 - wdW // 2, cur, wdW, wdH)
            cur += wdH + GAP
        if k == "dt" and dt["show"]:
            dtBase, dtW, dtH = digit_set(dt["color"], dt["size"], dtF)
            slashIdx, _, _ = small_text("/", dt["color"], dt["size"], dtF)
            tops["dt"] = (dtBase, slashIdx, cur, dtH)
            cur += dtH + GAP
    if "wd" in tops:
        base, wx, wy, ww, wh = tops["wd"]
        wd_js = {"X": wx, "Y": wy, "ImageIndex": base, "ImagesCount": 7}
    if "dt" in tops:
        base, slash, dy, dh = tops["dt"]
        dt_js = {
            "MonthAndDayAndYear": {
                "OneLine": {
                    "Number": {
                        "TopLeftX": 5,
                        "TopLeftY": dy,
                        "BottomRightX": 121,
                        "BottomRightY": dy + dh,
                        "Alignment": "Center",
                        "SpacingX": int(dt.get("spacing", 0)),
                        "SpacingY": 0,
                        "ImageIndex": base,
                        "ImagesCount": 10,
                    },
                    "DelimiterImageIndex": slash,
                },
                "TwoDigitsMonth": True,
                "TwoDigitsDay": True,
            }
        }
    topBottom = cur - GAP if tops else topY

    # ---- low rows ----
    LOW_ORDER = [
        "st",
        "di",
        "ca",
        "pu",
        "pai",
        "tmp",
        "hil",
        "hum",
        "wind",
        "uv",
        "al",
        "bp",
        "sn",
    ]
    cur = (
        max(cur, lowY) if False else lowY
    )  # low block starts at lowY (may overlap top/time if user pushes up)
    cur = lowY
    act = {}
    weather_js = {}
    alarm_js = batt_txt_js = status_js = None
    meta = {"lowRows": {}, "status": {}, "goalBar": None, "hil": None}
    seg_imgs = []

    def number_row(gid, extra_chars="", suffix_text=None, minus=False):
        g = G[gid]
        f = res_font(G, gid, gf)
        base, bw, bh = digit_set(g["color"], g["size"], f)
        extras = {}
        for ch in extra_chars:
            if ch == "/":
                continue
            ei, _, _ = small_text(ch, g["color"], g["size"], f)
            extras[ch] = ei
        suffix = None
        if suffix_text:
            suffix, _, _ = small_text(suffix_text, g["color"], g["size"], f)
        return base, bw, bh, extras, suffix

    for rid in LOW_ORDER:
        g = G[rid]
        if not g["show"]:
            continue
        f = res_font(G, rid, gf)
        if rid == "sn":
            # BT / Lock / DND status images at fixed x centers
            rowH = round(g["size"] * 1.1) + 4
            y0 = cur
            for key, cx, label in (
                ("bt", 30, "BT"),
                ("lock", 63, "LK"),
                ("dnd", 96, "DND"),
            ):
                on = text_img(label, g["size"], g["color"], f)
                oi = save(on)
                off = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
                fi = save(off)
                meta["status"][key] = {
                    "x": cx - on.width // 2,
                    "y": y0,
                    "w": on.width,
                    "h": on.height,
                    "on": oi,
                    "off": fi,
                }
            status_js = {"DoNotDisturb": {}, "Lock": {}, "Bluetooth": {}}
            # real StatusImage entries need coordinates; fill below
            cur += rowH + GAP
            meta["lowRows"]["sn"] = {"y": y0, "h": rowH}
            continue
        if rid == "hil":
            # hi/lo via Weather Today Separate Day/Night
            base_d, bwd, bhd, ex_d, suf_d = number_row("hil", suffix_text="°")
            minusIdx, _, _ = small_text("-", g["color"], g["size"], f)
            # second set for night (own indices; same look)
            base_n, _, _, _, _ = number_row("hil", suffix_text="°")
            if "Temperature" not in weather_js:
                weather_js["Temperature"] = {}
            weather_js["Temperature"]["Today"] = {
                "Separate": {
                    "Day": {
                        "Number": None,
                        "MinusImageIndex": minusIdx,
                        "SuffixImageIndex": suf_d,
                    },
                    "Night": {
                        "Number": None,
                        "MinusImageIndex": minusIdx,
                        "SuffixImageIndex": suf_d,
                    },
                }
            }
            # stash numbers; fill boxes after measuring row width below
            meta["hil"] = {
                "dayBase": base_d,
                "nightBase": base_n,
                "bw": bwd,
                "bh": bhd,
                "minus": minusIdx,
                "suffix": suf_d,
                "spacing": int(g.get("spacing", 0)),
            }
            rowH = bhd
            meta["lowRows"]["hil"] = {"y": cur, "h": rowH}
            cur += rowH + GAP
            continue
        if rid == "di":
            base, bw, bh, ex, _ = number_row("di")
            dotI, _, _ = small_text(".", g["color"], g["size"], f)
            kmI, _, _ = small_text("km", g["color"], g["size"], f)
            miI, _, _ = small_text("mi", g["color"], g["size"], f)
            act["Distance"] = {
                "Number": None,
                "KmSuffixImageIndex": kmI,
                "DecimalPointImageIndex": dotI,
                "MilesSuffixImageIndex": miI,
            }
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            act["Distance"]["Number"] = box
            meta["lowRows"]["di"] = {
                "y": cur,
                "h": bh,
                "base": base,
                "dot": dotI,
                "km": kmI,
                "mi": miI,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            continue
        if rid == "ca":
            base, bw, bh, ex, suf = number_row("ca", suffix_text="kcal")
            act["Calories"] = {"Number": None, "SuffixImageIndex": suf}
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            act["Calories"]["Number"] = box
            meta["lowRows"]["ca"] = {
                "y": cur,
                "h": bh,
                "base": base,
                "suffix": suf,
                "suffixW": None,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            continue
        if rid in ("st", "pu", "pai"):
            base, bw, bh, ex, suf = number_row(rid)
            key = {"st": "Steps", "pu": "Pulse", "pai": "PAI"}[rid]
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            act[key] = {"Number": box}
            meta["lowRows"][rid] = {
                "y": cur,
                "h": bh,
                "base": base,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            if rid == "st" and d.get("goalBar"):
                # 10 segment boxes under steps row
                sy = cur
                n, sw, gp = 10, 8, 2
                tot = n * sw + (n - 1) * gp
                x0 = 63 - tot // 2
                seg0 = alloc(10)
                for i in range(10):
                    img = Image.new("RGBA", (sw, 6), (0, 0, 0, 0))
                    dd = ImageDraw.Draw(img)
                    dd.rectangle([0, 0, sw - 1, 5], fill=g["color"])
                    img.save(out / f"{seg0 + i}.png")
                segs = [{"X": x0 + i * (sw + gp), "Y": sy} for i in range(10)]
                meta["goalBar"] = {"start": seg0, "segs": segs}
                cur += 6 + GAP
            continue
        if rid in ("tmp", "hum", "wind", "uv"):
            base, bw, bh, ex, suf = number_row(
                rid,
                suffix_text={"tmp": "°", "hum": "%", "wind": "m/s", "uv": "UV"}[rid],
            )
            minusIdx = None
            if rid == "tmp":
                minusIdx, _, _ = small_text("-", g["color"], g["size"], f)
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            if rid == "tmp":
                weather_js["Temperature"] = {
                    "Current": {
                        "Number": box,
                        "MinusImageIndex": minusIdx,
                        "SuffixImageIndex": suf,
                    }
                }
            elif rid == "hum":
                weather_js["Humidity"] = {"Number": box, "SuffixImageIndex": suf}
            elif rid == "wind":
                weather_js["Wind"] = {"Number": box, "SuffixImageIndexEN": suf}
            elif rid == "uv":
                weather_js["UVIndex"] = {"UV": {"Number": box, "SuffixImageIndex": suf}}
            meta["lowRows"][rid] = {
                "y": cur,
                "h": bh,
                "base": base,
                "suffix": suf,
                "minus": minusIdx,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            continue
        if rid == "al":
            base, bw, bh, ex, suf = number_row("al")
            colonA, _, _ = small_text(":", g["color"], g["size"], f)
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            transparent = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            onI = save(transparent.copy())
            offI = save(transparent.copy())
            nodI = save(transparent.copy())
            alarm_js = {
                "Number": box,
                "DelimiterImageIndex": colonA,
                "OnImage": None,
                "OffImage": None,
                "NoDataImage": None,
                "_on": onI,
                "_off": offI,
                "_nod": nodI,
            }
            meta["lowRows"]["al"] = {
                "y": cur,
                "h": bh,
                "base": base,
                "delim": colonA,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            continue
        if rid == "bp":
            base, bw, bh, ex, suf = number_row("bp", suffix_text="%")
            box = {
                "TopLeftX": 5,
                "TopLeftY": cur,
                "BottomRightX": 121,
                "BottomRightY": cur + bh,
                "Alignment": "Center",
                "SpacingX": int(g.get("spacing", 0)),
                "SpacingY": 0,
                "ImageIndex": base,
                "ImagesCount": 10,
            }
            batt_txt_js = {"Number": box, "SuffixImageIndex": suf}
            meta["lowRows"]["bp"] = {
                "y": cur,
                "h": bh,
                "base": base,
                "suffix": suf,
                "spacing": int(g.get("spacing", 0)),
            }
            cur += bh + GAP
            continue

    # ---- battery low-only icon ----
    BATT_W, BATT_H = 44, 22
    batt_x = (W - BATT_W) // 2
    for idx in range(6):
        make_battery_icon(idx).save(out / f"{alloc()}.png")
    batt_start = nxt[0] - 6
    batt_js = {
        "BatteryIcon": {"X": batt_x, "Y": battY, "ImageIndex": batt_start, "ImagesCount": 6}
    }
    if batt_txt_js:
        batt_js["BatteryText"] = batt_txt_js

    # Composite preview thumbnail (126x294) for on-band display and app preview
    preview_idx = alloc()
    meta["preview_idx"] = preview_idx
    preview_img = Image.open(out / "0.png").convert("RGBA")

    # 1. Weekday FRI
    if wd_js:
        fri_idx = wd_js["ImageIndex"] + 4
        if (out / f"{fri_idx}.png").exists():
            im_fri = Image.open(out / f"{fri_idx}.png")
            preview_img.paste(im_fri, (wd_js["X"], wd_js["Y"]), im_fri)
    # 2. Date 11/20
    if dt_js:
        nl = dt_js["MonthAndDayAndYear"]["OneLine"]
        n_idx = nl["Number"]["ImageIndex"]
        del_idx = nl["DelimiterImageIndex"]
        if (out / f"{n_idx + 1}.png").exists():
            im_d1 = Image.open(out / f"{n_idx + 1}.png")
            im_slash = Image.open(out / f"{del_idx}.png")
            im_d2 = Image.open(out / f"{n_idx + 2}.png")
            im_d0 = Image.open(out / f"{n_idx}.png")
            sp = nl["Number"].get("SpacingX", 1)
            tot_w = im_d1.width * 4 + im_slash.width + sp * 4
            dx = (nl["Number"]["TopLeftX"] + nl["Number"]["BottomRightX"] - tot_w) // 2
            dy = nl["Number"]["TopLeftY"]
            preview_img.paste(im_d1, (dx, dy), im_d1)
            dx += im_d1.width + sp
            preview_img.paste(im_d1, (dx, dy), im_d1)
            dx += im_d1.width + sp
            preview_img.paste(im_slash, (dx, dy), im_slash)
            dx += im_slash.width + sp
            preview_img.paste(im_d2, (dx, dy), im_d2)
            dx += im_d2.width + sp
            preview_img.paste(im_d0, (dx, dy), im_d0)
    # 3. Time 10:09
    if "Hours" in time_js and "Minutes" in time_js:
        th = time_js["Hours"]
        tm = time_js["Minutes"]
        h_idx = th["Tens"]["ImageIndex"]
        m_idx = tm["Tens"]["ImageIndex"]
        if (out / f"{h_idx + 1}.png").exists():
            im_h1 = Image.open(out / f"{h_idx + 1}.png")
            im_h0 = Image.open(out / f"{h_idx}.png")
            preview_img.paste(im_h1, (th["Tens"]["X"], th["Tens"]["Y"]), im_h1)
            preview_img.paste(im_h0, (th["Ones"]["X"], th["Ones"]["Y"]), im_h0)
        if (out / f"{m_idx}.png").exists():
            im_m0 = Image.open(out / f"{m_idx}.png")
            im_m9 = Image.open(out / f"{m_idx + 9}.png")
            preview_img.paste(im_m0, (tm["Tens"]["X"], tm["Tens"]["Y"]), im_m0)
            preview_img.paste(im_m9, (tm["Ones"]["X"], tm["Ones"]["Y"]), im_m9)
    # 4. Steps 8432
    if act and "Steps" in act:
        st_box = act["Steps"]["Number"]
        s_idx = st_box["ImageIndex"]
        if (out / f"{s_idx + 8}.png").exists():
            im_s8 = Image.open(out / f"{s_idx + 8}.png")
            im_s4 = Image.open(out / f"{s_idx + 4}.png")
            im_s3 = Image.open(out / f"{s_idx + 3}.png")
            im_s2 = Image.open(out / f"{s_idx + 2}.png")
            sp = st_box.get("SpacingX", 1)
            tot_w = im_s8.width + im_s4.width + im_s3.width + im_s2.width + sp * 3
            sx = (st_box["TopLeftX"] + st_box["BottomRightX"] - tot_w) // 2
            sy = st_box["TopLeftY"]
            preview_img.paste(im_s8, (sx, sy), im_s8)
            sx += im_s8.width + sp
            preview_img.paste(im_s4, (sx, sy), im_s4)
            sx += im_s4.width + sp
            preview_img.paste(im_s3, (sx, sy), im_s3)
            sx += im_s3.width + sp
            preview_img.paste(im_s2, (sx, sy), im_s2)
    # 5. Battery: representative orange LOW badge
    if (out / f"{batt_start + 1}.png").exists():
        im_batt = Image.open(out / f"{batt_start + 1}.png")
        preview_img.paste(im_batt, (batt_x, battY), im_batt)

    preview_img.convert("RGB").save(out / f"{preview_idx}.png")

    js = {
        "Background": {
            "Image": {"X": 0, "Y": 0, "ImageIndex": 0},
            "PreviewEN": {"X": 0, "Y": 0, "ImageIndex": preview_idx},
            "PreviewCN": {"X": 0, "Y": 0, "ImageIndex": preview_idx},
            "PreviewCN2": {"X": 0, "Y": 0, "ImageIndex": preview_idx},
        },
        "Time": time_js,
    }
    if act:
        act["UnknownV7"] = 0
        js["Activity"] = act
    if dt_js or wd_js:
        js["Date"] = {}
        if dt_js:
            js["Date"].update(dt_js)
        if wd_js:
            js["Date"]["ENWeekDays"] = wd_js
    if weather_js:
        # finalize hil Separate numbers with centered row boxes
        if (
            "Temperature" in weather_js
            and "Today" in weather_js["Temperature"]
            and meta["hil"]
        ):
            mh = meta["hil"]
            # each of day/night gets half row: day centered in left half, night in right half
            dayBox = {
                "TopLeftX": 5,
                "TopLeftY": meta["lowRows"]["hil"]["y"],
                "BottomRightX": 60,
                "BottomRightY": meta["lowRows"]["hil"]["y"] + mh["bh"],
                "Alignment": "Center",
                "SpacingX": mh["spacing"],
                "SpacingY": 0,
                "ImageIndex": mh["dayBase"],
                "ImagesCount": 10,
            }
            nightBox = dict(
                dayBox, TopLeftX=66, BottomRightX=121, ImageIndex=mh["nightBase"]
            )
            weather_js["Temperature"]["Today"]["Separate"]["Day"]["Number"] = dayBox
            weather_js["Temperature"]["Today"]["Separate"]["Night"]["Number"] = nightBox
            meta["hil"]["dayBox"] = dayBox
            meta["hil"]["nightBox"] = nightBox
        js["Weather"] = weather_js
    if meta["goalBar"]:
        js["StepsProgress"] = {
            "Linear": {
                "StartImageIndex": meta["goalBar"]["start"],
                "Segments": meta["goalBar"]["segs"],
            }
        }
    if status_js is not None:
        st_map = {}
        for key, skey in (
            ("bt", "Bluetooth"),
            ("lock", "Lock"),
            ("dnd", "DoNotDisturb"),
        ):
            m = meta["status"][key]
            st_map[skey] = {
                "Coordinates": {
                    "X": m["x"],
                    "Y": m["y"],
                    "Alignment": "Center",
                    "Unknown4": 0,
                    "Unknown5": 0,
                },
                "OnImageIndex": m["on"],
                "OffImageIndex": m["off"],
            }
        js["Status"] = st_map
    js["Battery"] = batt_js
    if alarm_js is not None:
        a = alarm_js
        js["Alarm"] = {
            "Number": a["Number"],
            "DelimiterImageIndex": a["DelimiterImageIndex"],
            "OnImage": {"X": 0, "Y": 0, "ImageIndex": a["_on"]},
            "OffImage": {"X": 0, "Y": 0, "ImageIndex": a["_off"]},
            "NoDataImage": {"X": 0, "Y": 0, "ImageIndex": a["_nod"]},
            "UnknownV6": 0,
            "UnknownV7": 0,
        }

    (out / "watchface.json").write_text(json.dumps(js, indent=2))
    # resolve suffix image widths for preview centering
    for rid, m in list(meta["lowRows"].items()):
        if "suffix" in m and m["suffix"]:
            try:
                im = Image.open(out / f"{m['suffix']}.png")
                m["suffixW"] = im.width
            except Exception:
                m["suffixW"] = None
    # content bounds (band is 126x294) so the UI can warn about clipping
    if layout_mode == "stack":
        timeBottom = (SS_Y + ssBH) if ss["show"] else (MM_Y + BH2)
    else:
        timeBottom = timeY + max(BH, BH2)
    lowBottom = cur - GAP if meta["lowRows"] else lowY
    battBottom = battY + BATT_H
    meta["bounds"] = {
        "topTop": topY,
        "topBottom": topBottom,
        "timeTop": timeY,
        "timeBottom": timeBottom,
        "timeBW": BW,
        "timeBH": BH,
        "timeBW2": BW2,
        "timeBH2": BH2,
        "lowTop": lowY,
        "lowBottom": lowBottom,
        "battTop": battY,
        "battBottom": battBottom,
    }
    meta["overflowPx"] = max(0, timeBottom - H, lowBottom - H, battBottom - H)
    errors = validate_hardware(js, meta, layout_mode, ss["show"])
    meta["validationErrors"] = errors
    meta["valid"] = len(errors) == 0
    if errors:
        print(f"WARNING: Mi Band 5 hardware constraint violations:")
        for err in errors:
            print(f"  - {err}")
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"clean-night-18-custom {len(list(out.glob('*.png')))} images, valid={meta['valid']}")
    return js, meta


def validate_hardware(js, meta, layout_mode, ss_show):
    errors = []
    b = meta.get("bounds", {})

    if meta.get("overflowPx", 0) > 0:
        errors.append(f"Content overflows screen height (294px) by {meta['overflowPx']}px")

    time = js.get("Time", {})
    if "Hours" in time:
        h = time["Hours"]
        if "Tens" in h and "Ones" in h:
            tx, ox = h["Tens"]["X"], h["Ones"]["X"]
            bw = b.get("timeBW", 42)
            if ox < tx + bw:
                errors.append(f"Hours Tens (X={tx}, W={bw}) and Ones (X={ox}) overlap by {tx + bw - ox}px")
            if tx < 0 or ox + bw > W:
                errors.append(f"Hours digits exceed screen width (0..126px)")

    if "Minutes" in time:
        m = time["Minutes"]
        if "Tens" in m and "Ones" in m:
            tx, ox = m["Tens"]["X"], m["Ones"]["X"]
            bw2 = b.get("timeBW2", 42)
            if ox < tx + bw2:
                errors.append(f"Minutes Tens (X={tx}, W={bw2}) and Ones (X={ox}) overlap by {tx + bw2 - ox}px")
            if tx < 0 or ox + bw2 > W:
                errors.append(f"Minutes digits exceed screen width (0..126px)")

    if layout_mode == "stack":
        hy = time["Hours"]["Tens"]["Y"]
        my = time["Minutes"]["Tens"]["Y"]
        bh = b.get("timeBH", 62)
        if my < hy + bh:
            errors.append(f"Hours (Y={hy}, H={bh}) and Minutes (Y={my}) overlap by {hy + bh - my}px")
        if ss_show and "Seconds" in time:
            sy = time["Seconds"]["Tens"]["Y"]
            bh2 = b.get("timeBH2", 62)
            if sy < my + bh2:
                errors.append(f"Minutes (Y={my}, H={bh2}) and Seconds (Y={sy}) overlap by {my + bh2 - sy}px")

    top_bottom = b.get("topBottom", 0)
    time_top = b.get("timeTop", 0)
    time_bottom = b.get("timeBottom", 0)
    low_top = b.get("lowTop", 0)
    low_bottom = b.get("lowBottom", 0)
    batt_top = b.get("battTop", 0)
    batt_bottom = b.get("battBottom", 0)

    if top_bottom > time_top:
        errors.append(f"Top block (bottom={top_bottom}) overlaps Time (top={time_top})")

    # Battery can be placed either between Time and Low (battTop < lowTop), or below Low (battTop >= lowTop)
    if batt_top < low_top:
        if time_bottom > batt_top:
            errors.append(f"Time block (bottom={time_bottom}) overlaps Battery (top={batt_top})")
        if batt_bottom > low_top and meta.get("lowRows"):
            errors.append(f"Battery (bottom={batt_bottom}) overlaps Activity/Low (top={low_top})")
        if low_bottom > 294:
            errors.append(f"Activity/Low (bottom={low_bottom}) overflows bottom of screen (294px)")
    else:
        if time_bottom > low_top and meta.get("lowRows"):
            errors.append(f"Time block (bottom={time_bottom}) overlaps Activity/Low (top={low_top})")
        if low_bottom > batt_top and meta.get("lowRows"):
            errors.append(f"Activity/Low block (bottom={low_bottom}) overlaps Battery (top={batt_top})")
        if batt_bottom > 294:
            errors.append(f"Battery (bottom={batt_bottom}) overflows bottom of screen (294px)")

    # Hardware sprite buffer check (Mi Band 5 display blitter has a 4KB / 4096-byte line buffer limit)
    # In format 0x64 (8bpp indexed): binary sprite size = 16 (header) + 1024 (palette) + W*H bytes.
    # Therefore, any sprite with area W*H > 3056 px (1040 + 3056 = 4096 B) exceeds the hardware buffer.
    bw = b.get("timeBW", 42)
    bh = b.get("timeBH", 62)
    if bw * bh > 3056:
        errors.append(f"Hours sprite size ({bw}x{bh} = {bw * bh}px) exceeds 4KB hardware buffer limit (max 3056px)")
    bw2 = b.get("timeBW2", 42)
    bh2 = b.get("timeBH2", 62)
    if bw2 * bh2 > 3056:
        errors.append(f"Minutes sprite size ({bw2}x{bh2} = {bw2 * bh2}px) exceeds 4KB hardware buffer limit (max 3056px)")

    out_dir = ROOT / "faces" / "clean-night-18-custom"
    preview_idx = meta.get("preview_idx", 45)
    for p in out_dir.glob("*.png"):
        if not p.stem.isdigit():
            continue
        idx = int(p.stem)
        if idx == 0 or idx == preview_idx:
            continue
        try:
            im = Image.open(p)
            area = im.width * im.height
            if area > 3056:
                errors.append(f"Sprite {p.name} ({im.width}x{im.height} = {area}px) exceeds 4KB hardware buffer limit")
            if im.mode == "RGBA":
                alphas = set(im.getchannel("A").get_flattened_data())
                if not alphas.issubset({0, 255}):
                    errors.append(f"Sprite {p.name} contains partial alpha (must be 1-bit alpha for 0x64 encoding)")
        except Exception:
            pass

    return errors


def main():
    d = DEFAULT_DESIGN()
    if DESIGN.exists():
        try:
            saved = json.loads(DESIGN.read_text())
            for k, v in saved.items():
                if k in ("groups", "values", "y"):
                    d[k].update(v)
                else:
                    d[k] = v
        except Exception as e:
            print("design load failed, using defaults:", e)
    else:
        DESIGN.write_text(json.dumps(d, indent=1))
    if len(sys.argv) > 1:
        d.update(json.loads(Path(sys.argv[1]).read_text()))
    js, meta = build(d)
    if not meta.get("valid", False):
        print(f"ERROR: Build failed hardware validation: {meta.get('validationErrors')}")
        sys.exit(1)

    bin_dir = ROOT / "bin"
    bin_dir.mkdir(exist_ok=True)
    packed = ROOT / "clean-night-18-custom_packed.bin"
    if packed.exists():
        packed.unlink()
    r = subprocess.run(
        ["./node_modules/.bin/wfjs", "writeBin", "-i", "faces/clean-night-18-custom", "-m", "miband5"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"wfjs packaging error: {r.stderr}")
        sys.exit(1)
    target = bin_dir / "clean-night-18-custom.bin"
    if packed.exists():
        packed.replace(target)
    print(f"Packaged {target} ({target.stat().st_size} bytes)")

    # Verify hardware safety: parse the packed binary
    verify_script = f"""
const fs = require('fs');
const {{ getAvailableModels, parseWatchFaceBin }} = require('./node_modules/watchface-js/dist/watchFaceBinTools/watchFaceBinParser.js');
const mb5 = getAvailableModels().find(m => m.id === 'miband5');
const buf = fs.readFileSync('{target}');
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const wf = parseWatchFaceBin(ab, mb5.fileType);
const previewIdx = wf.parameters.Background && wf.parameters.Background.PreviewEN ? wf.parameters.Background.PreviewEN.ImageIndex : -1;
for (let i = 0; i < wf.images.length; i++) {{
  const img = wf.images[i];
  if (i !== 0 && i !== previewIdx) {{
    if (img.pixelFormat !== 0x64) {{
      throw new Error(`Image ${{i}} format 0x${{img.pixelFormat.toString(16)}} (expected 0x64 indexed colors)`);
    }}
    const bSize = 16 + 1024 + img.width * img.height;
    if (bSize > 4096) {{
      throw new Error(`Image ${{i}} (${{img.width}}x${{img.height}}) size ${{bSize}}B exceeds 4KB buffer`);
    }}
  }}
}}
console.log('clean-night-18-custom verified hardware-safe (0x64 indexed, <= 4096 bytes)');
"""
    v = subprocess.run(
        ["node", "-e", verify_script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if v.returncode != 0:
        raise RuntimeError(
            f"Hardware safety check failed for clean-night-18-custom: {v.stderr}"
        )
    print(v.stdout.strip())

    win_dl = Path("/mnt/c/Users/Karoly/Downloads")
    if win_dl.exists():
        shutil.copy2(target, win_dl / "clean-night-18-custom.bin")
        print(f"Copied clean-night-18-custom.bin to {win_dl}")

    subprocess.run(["python3", str(ROOT / "scripts" / "gen_exact.py")], check=True)



if __name__ == "__main__":
    main()
