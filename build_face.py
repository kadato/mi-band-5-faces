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


def glyph(ch, w, h, size, color, fname):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font_for(fname, size)
    bb = d.textbbox((0, 0), ch, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]), ch, font=f, fill=color)
    return img


def text_img(s, size, color, fname, pad=2):
    f = font_for(fname, size)
    tmp = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bb[0], pad - bb[1]), s, font=f, fill=color)
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
        "rowGap": -25,
        "y": {"top": 6, "time": 62, "low": 234, "batt": 264},
        "groups": {
            "hh": g("#c0caf5", 78, True, "global", 0),
            "mm": g("#c0caf5", 78, True, "global", 0),
            "ss": g("#565f89", 26, False, "global", 0),
            "wd": g("#7aa2f7", 18, True, "global", 2),
            "dt": g("#7aa2f7", 22, True, "global", 0),
            "st": g("#7aa2f7", 24, True, "global", 0),
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
        bw, bh = box if box else (round(size * 0.82), round(size * 1.09))
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
    BH = round(int(hh["size"]) / 0.87)
    BW = round(BH * 2 / 3)
    tfont = round(BH * 0.87)
    mmSize = int(mm["size"])
    BH2 = round(mmSize / 0.87)
    BW2 = round(BH2 * 2 / 3)
    tfont2 = round(BH2 * 0.87)
    if ss["show"]:
        ssTfont = round(int(ss["size"]) / 0.87)
        ssBH = round(int(ss["size"]) / 0.87)
        ssBW = round(ssBH * 2 / 3)
        ssTfont = round(ssBH * 0.87)
    else:
        ssBH = ssBW = ssTfont = 0
    if layout_mode == "side":
        # measure colon at requested size, then shrink everything to fit 116px
        _ci = text_img(delim, tfont, hh["color"], hhF)
        _cw = _ci.width
        _sp = int(hh.get("spacing", 0))
        _sp2 = int(mm.get("spacing", 0))
        _tot = (2 * BW - 20 + _sp) + _cw + 6 + (2 * BW2 - 20 + _sp2)
        if ss["show"]:
            _tot += _cw + 6 + (2 * ssBW - 20 + int(ss.get("spacing", 0)))
        if _tot > 116:
            f = 116 / _tot
            BH, BW = max(8, round(BH * f)), max(6, round(BW * f))
            tfont = max(6, round(tfont * f))
            BH2, BW2 = max(8, round(BH2 * f)), max(6, round(BW2 * f))
            tfont2 = max(6, round(tfont2 * f))
            if ss["show"]:
                ssBH, ssBW = max(8, round(ssBH * f)), max(6, round(ssBW * f))
                ssTfont = max(6, round(ssTfont * f))
    hhBase, _, _ = digit_set(hh["color"], tfont, hhF, box=(BW, BH))
    # time cells use BW x BH boxes
    if linked:
        mmBase = hhBase
        BW2, BH2, tfont2 = BW, BH, tfont
    else:
        mmBase, _, _ = digit_set(mm["color"], tfont2, mmF, box=(BW2, BH2))
    ssBase = None
    if ss["show"]:
        ssBase, _, _ = digit_set(ss["color"], ssTfont, ssF, box=(ssBW, ssBH))
    colonIdx = colonW = colonH = None
    if layout_mode == "side":
        colonIdx, colonW, colonH = small_text(delim, hh["color"], tfont, hhF)

    sp = int(hh.get("spacing", 0))
    step = BW - 20 + sp
    MM_Y = timeY + BH + gap
    if layout_mode == "stack":
        HH_X0 = 63 - (2 * BW - 20 + sp) // 2
        HH_X1 = HH_X0 + step
        MM_X0, MM_X1 = HH_X0, HH_X1
        if ss["show"]:
            sstep = ssBW - 20 + int(ss.get("spacing", 0))
            SS_X0 = 63 - (2 * ssBW - 20 + int(ss.get("spacing", 0))) // 2
            SS_X1 = SS_X0 + sstep
        else:
            SS_X0 = SS_X1 = HH_X0
        SS_Y = MM_Y + BH2 + GAP
    else:
        # side: HH tens/ones, delim, MM tens/ones [, delim, SS tens/ones]
        step2 = BW2 - 20 + int(mm.get("spacing", 0))
        parts = [2 * BW - 20 + sp, colonW + 6, 2 * BW2 - 20 + int(mm.get("spacing", 0))]
        if ss["show"]:
            parts += [colonW + 6, 2 * ssBW - 20 + int(ss.get("spacing", 0))]
        total = sum(parts)
        x = 63 - total // 2
        HH_X0, HH_X1 = x, x + step
        x += 2 * BW - 20 + sp
        dx = x + 3
        x += colonW + 6
        MM_X0, MM_X1 = x, x + step2
        x += 2 * BW2 - 20 + int(mm.get("spacing", 0))
        SS_X0 = SS_X1 = None
        if ss["show"]:
            x += 3  # second delim pos ~ dx2
            dx2 = x
            x += colonW + 6
            sstep = ssBW - 20 + int(ss.get("spacing", 0))
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

    js = {"Background": {"Image": {"X": 0, "Y": 0, "ImageIndex": 0}}, "Time": time_js}
    if dt_js or wd_js:
        js["Date"] = {}
        if dt_js:
            js["Date"].update(dt_js)
        if wd_js:
            js["Date"]["ENWeekDays"] = wd_js
    if act:
        js["Activity"] = act
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
    js["Battery"] = batt_js

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
        timeBottom = timeY + BH
    lowBottom = cur - GAP  # cur already advanced past last row gap
    meta["bounds"] = {
        "timeBottom": timeBottom,
        "lowBottom": lowBottom,
        "battBottom": battY + BATT_H,
    }
    meta["overflowPx"] = max(0, timeBottom - H, lowBottom - H, (battY + BATT_H) - H)
    (out / "meta.json").write_text(json.dumps(meta))
    print(f"clean-night-18-custom {len(list(out.glob('*.png')))} images")
    return js, meta


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
    build(d)


if __name__ == "__main__":
    main()
