#!/usr/bin/env python3
"""Emit faces.js: layout + image index for the studio's exact-pixel mode.
The studio then draws the real .bin PNGs on canvas, pixel identical."""

from pathlib import Path
import json

ROOT = Path("/home/karoly/projects/mi-band-5-faces")
FACES = [
    "clean-night-10-blue",
    "clean-night-11-mono",
    "clean-night-12-volt",
    "clean-night-13-aqua",
    "clean-night-14-ember",
    "clean-night-15-duo-frost",
    "clean-night-16-duo-sky",
    "clean-night-17-duo-deep",
    "clean-night-18-custom",
]
out = {"faces": {}}
for name in FACES:
    d = ROOT / name
    layout = json.loads((d / "watchface.json").read_text())
    ids = {0}

    def collect(o):
        if isinstance(o, dict):
            if "ImageIndex" in o and "ImagesCount" in o:
                ids.update(range(o["ImageIndex"], o["ImageIndex"] + o["ImagesCount"]))
            if "DelimiterImageIndex" in o:
                ids.add(o["DelimiterImageIndex"])
            if "SuffixImageIndex" in o:
                ids.add(o["SuffixImageIndex"])
            for v in o.values():
                collect(v)

    collect(layout)
    missing = [i for i in sorted(ids) if not (d / f"{i}.png").exists()]
    out["faces"][name] = {
        "dir": name,
        "ids": sorted(ids),
        "layout": layout,
        "gapBuilt": (
            layout["Time"]["Minutes"]["Tens"]["Y"]
            - layout["Time"]["Hours"]["Tens"]["Y"]
            - 80
        )
        * 2,
        "missing": missing,
    }
    print(name, len(ids), "images", "MISSING:", missing if missing else "ok")
(ROOT / "faces.js").write_text("const FACES = " + json.dumps(out) + ";")
print("faces.js written")
