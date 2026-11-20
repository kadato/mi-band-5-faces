#!/usr/bin/env python3
"""Generate pixel-exact 2x preview PNG images from watch face assets."""

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def render_face(face_name, hh="12", mm="45", date_str="11/17", day_str="WED", steps="8432", batt_pct=85):
    face_dir = ROOT / "faces" / face_name
    wf = json.loads((face_dir / "watchface.json").read_text())

    canvas = Image.new("RGBA", (126, 294), (0, 0, 0, 255))
    bg = Image.open(face_dir / "0.png")
    canvas.paste(bg, (0, 0))

    # Time: Hours and Minutes
    time_cfg = wf.get("Time", {})
    if "Hours" in time_cfg:
        th = time_cfg["Hours"]
        h0 = Image.open(face_dir / f"{th['Tens']['ImageIndex'] + int(hh[0])}.png")
        h1 = Image.open(face_dir / f"{th['Ones']['ImageIndex'] + int(hh[1])}.png")
        canvas.paste(h0, (th["Tens"]["X"], th["Tens"]["Y"]), h0)
        canvas.paste(h1, (th["Ones"]["X"], th["Ones"]["Y"]), h1)
    if "Minutes" in time_cfg:
        tm = time_cfg["Minutes"]
        m0 = Image.open(face_dir / f"{tm['Tens']['ImageIndex'] + int(mm[0])}.png")
        m1 = Image.open(face_dir / f"{tm['Ones']['ImageIndex'] + int(mm[1])}.png")
        canvas.paste(m0, (tm["Tens"]["X"], tm["Tens"]["Y"]), m0)
        canvas.paste(m1, (tm["Ones"]["X"], tm["Ones"]["Y"]), m1)

    # Date and Weekday
    date_cfg = wf.get("Date", {})
    if "MonthAndDayAndYear" in date_cfg and "OneLine" in date_cfg["MonthAndDayAndYear"]:
        num_cfg = date_cfg["MonthAndDayAndYear"]["OneLine"]["Number"]
        del_idx = date_cfg["MonthAndDayAndYear"]["OneLine"].get("DelimiterImageIndex")
        imgs = []
        for ch in date_str:
            if ch.isdigit():
                imgs.append(Image.open(face_dir / f"{num_cfg['ImageIndex'] + int(ch)}.png"))
            elif ch == "/" and del_idx is not None:
                imgs.append(Image.open(face_dir / f"{del_idx}.png"))
        sp = num_cfg.get("SpacingX", 0)
        tot = sum(im.width for im in imgs) + sp * (len(imgs) - 1)
        tlx, tly = num_cfg["TopLeftX"], num_cfg["TopLeftY"]
        brx, bry = num_cfg["BottomRightX"], num_cfg["BottomRightY"]
        align = num_cfg.get("Alignment", "Center")
        x = (tlx + brx - tot) // 2 if align == "Center" else tlx
        ymid = (tly + bry) // 2
        for im in imgs:
            canvas.paste(im, (x, ymid - im.height // 2), im)
            x += im.width + sp

    if "ENWeekDays" in date_cfg:
        wd_cfg = date_cfg["ENWeekDays"]
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        di = days.index(day_str) if day_str in days else 0
        wdim = Image.open(face_dir / f"{wd_cfg['ImageIndex'] + di}.png")
        canvas.paste(wdim, (wd_cfg["X"], wd_cfg["Y"]), wdim)

    # Steps
    act_cfg = wf.get("Activity", {})
    if "Steps" in act_cfg and "Number" in act_cfg["Steps"]:
        sn_cfg = act_cfg["Steps"]["Number"]
        imgs = [Image.open(face_dir / f"{sn_cfg['ImageIndex'] + int(ch)}.png") for ch in steps]
        sp = sn_cfg.get("SpacingX", 0)
        tot = sum(im.width for im in imgs) + sp * (len(imgs) - 1)
        tlx, tly = sn_cfg["TopLeftX"], sn_cfg["TopLeftY"]
        brx, bry = sn_cfg["BottomRightX"], sn_cfg["BottomRightY"]
        align = sn_cfg.get("Alignment", "Center")
        x = (tlx + brx - tot) // 2 if align == "Center" else tlx
        ymid = (tly + bry) // 2
        for im in imgs:
            canvas.paste(im, (x, ymid - im.height // 2), im)
            x += im.width + sp

    # Battery
    batt_cfg = wf.get("Battery", {})
    if "BatteryIcon" in batt_cfg:
        bi_cfg = batt_cfg["BatteryIcon"]
        if batt_pct < 10:
            idx = 0
        elif batt_pct < 20:
            idx = 1
        else:
            idx = min(bi_cfg["ImagesCount"] - 1, 2 + (batt_pct - 20) // 20)
        bim = Image.open(face_dir / f"{bi_cfg['ImageIndex'] + idx}.png")
        if bim.getbbox() is not None:
            canvas.paste(bim, (bi_cfg["X"], bi_cfg["Y"]), bim)

    return canvas.resize((252, 588), Image.NEAREST)


def main():
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)

    demos = [
        ("demo-volt-low.png", "clean-night-12-volt", 12),
        ("demo-volt-normal.png", "clean-night-12-volt", 85),
        ("demo-batt-low.png", "clean-night-10-blue", 12),
        ("demo-batt-critical.png", "clean-night-10-blue", 5),
        ("demo-batt-normal.png", "clean-night-10-blue", 85),
        ("demo-blue-normal.png", "clean-night-10-blue", 85),
        ("demo-blue-low.png", "clean-night-10-blue", 12),
        ("demo-blue-low2.png", "clean-night-10-blue", 12),
        ("demo-blue-critical.png", "clean-night-10-blue", 5),
        ("demo-blue-critical2.png", "clean-night-10-blue", 5),
        ("demo-duo-sky.png", "clean-night-16-duo-sky", 85),
        ("demo-duo-volt.png", "clean-night-12-volt", 85),
        ("demo-custom-normal.png", "clean-night-18-custom", 85),
        ("demo-custom-low.png", "clean-night-18-custom", 12),
        ("demo-custom-critical.png", "clean-night-18-custom", 5),
        ("demo-layout-low.png", "clean-night-18-custom", 12),
        ("demo-tight-low.png", "clean-night-18-custom", 12),
    ]

    for filename, face_name, batt_pct in demos:
        img = render_face(face_name, batt_pct=batt_pct)
        target = assets / filename
        img.save(target)
        print(f"Generated {target.name} from {face_name} (battery {batt_pct}%)")


if __name__ == "__main__":
    main()
