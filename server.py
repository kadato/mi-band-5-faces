#!/usr/bin/env python3
"""Design-app server for Mi Band 5 faces.

Serves preview.html + face PNGs, rebuilds clean-night-18-custom from
POSTed design JSON. Single source of truth: build_face.py output.
Preview draws those PNGs, so preview == .bin pixels.

Run: python3 server.py [port]  (default 8903)
"""

import copy
import json
import shutil
import subprocess
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_face import build

DESIGN = ROOT / "custom-design.json"
BUILD_ID = ROOT / ".build_id"


def read_design():
    from build_face import DEFAULT_DESIGN

    dflt = DEFAULT_DESIGN()
    try:
        d = json.loads(DESIGN.read_text())
    except Exception:
        d = {}
    # self-heal: fill missing keys / groups from defaults
    for k, v in dflt.items():
        if k not in d:
            d[k] = copy.deepcopy(v)
    if isinstance(d.get("groups"), dict):
        for gid, gd in dflt["groups"].items():
            if gid not in d["groups"] or not isinstance(d["groups"][gid], dict):
                d["groups"][gid] = copy.deepcopy(gd)
            else:
                for fk, fv in gd.items():
                    if fk not in d["groups"][gid]:
                        d["groups"][gid][fk] = fv
    for k in ("y", "values"):
        if isinstance(d.get(k), dict):
            for fk, fv in dflt[k].items():
                if fk not in d[k]:
                    d[k][fk] = fv
    return d


def write_design(d):
    DESIGN.write_text(json.dumps(d))


def refresh_faces_entry(layout, meta):
    """Update only the 18-custom entry in faces.js (keep other faces)."""
    p = ROOT / "faces.js"
    txt = p.read_text()
    data = json.loads(txt.split("=", 1)[1].strip().rstrip(";"))

    def collect(o, ids):
        if isinstance(o, dict):
            if "ImageIndex" in o and "ImagesCount" in o:
                ids.update(range(o["ImageIndex"], o["ImageIndex"] + o["ImagesCount"]))
            if "DelimiterImageIndex" in o:
                ids.add(o["DelimiterImageIndex"])
            if "SuffixImageIndex" in o:
                ids.add(o["SuffixImageIndex"])
            if "MinusImageIndex" in o:
                ids.add(o["MinusImageIndex"])
            for k in (
                "KmSuffixImageIndex",
                "MilesSuffixImageIndex",
                "DecimalPointImageIndex",
                "OnImage",
                "OffImage",
                "NoDataImage",
            ):
                v = o.get(k)
                if isinstance(v, int):
                    ids.add(v)
            for v in o.values():
                collect(v, ids)

    ids = {0}
    collect(layout, ids)
    try:
        gap = (
            layout["Time"]["Minutes"]["Tens"]["Y"]
            - layout["Time"]["Hours"]["Tens"]["Y"]
            - 80
        ) * 2
    except KeyError:
        gap = 0
    files = {
        int(p.stem)
        for p in (ROOT / "faces" / "clean-night-18-custom").glob("*.png")
        if p.stem.isdigit()
    }
    data["faces"]["clean-night-18-custom"] = {
        "dir": "faces/clean-night-18-custom",
        "ids": sorted(ids),
        "layout": layout,
        "meta": meta,
        "gapBuilt": gap,
        "missing": [i for i in sorted(ids) if i not in files],
    }
    p.write_text("const FACES = " + json.dumps(data) + ";")
    return data["faces"]["clean-night-18-custom"]


def pack_bin():
    packed = ROOT / "clean-night-18-custom_packed.bin"
    if packed.exists():
        packed.unlink()
    r = subprocess.run(
        [
            "./node_modules/.bin/wfjs",
            "writeBin",
            "-i",
            "faces/clean-night-18-custom",
            "-m",
            "miband5",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"wfjs failed: {r.stderr[-2000:]}")
    target_dir = ROOT / "bin"
    target_dir.mkdir(exist_ok=True)
    target = target_dir / "clean-night-18-custom.bin"
    if packed.exists():
        packed.replace(target)
    # Hardware safety verification
    verify_script = f"""
const fs = require('fs');
const {{ getAvailableModels, parseWatchFaceBin }} = require('./node_modules/watchface-js/dist/watchFaceBinTools/watchFaceBinParser.js');
const mb5 = getAvailableModels().find(m => m.id === 'miband5');
const buf = fs.readFileSync('{target}');
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const wf = parseWatchFaceBin(ab, mb5.fileType);
const previewIdx = wf.parameters.Background && wf.parameters.Background.PreviewEN ? wf.parameters.Background.PreviewEN.ImageIndex : -1;

if (wf.parameters.Time && wf.parameters.Time.DrawingOrder !== false) {{
  throw new Error('Time.DrawingOrder must be false (Protobuf tag 11)');
}}
if (wf.parameters.Activity && wf.parameters.Activity.UnknownV7 !== 0) {{
  throw new Error('Activity.UnknownV7 must be 0 (Protobuf tag 7)');
}}
if (wf.parameters.Time && wf.parameters.Time.Hours && wf.parameters.Time.Minutes) {{
  if (wf.parameters.Time.Hours.Tens.ImageIndex === wf.parameters.Time.Minutes.Tens.ImageIndex) {{
    throw new Error('Hours and Minutes must have distinct ImageIndex sets');
  }}
}}

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
"""
    v = subprocess.run(
        ["node", "-e", verify_script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if v.returncode != 0:
        raise RuntimeError(f"Hardware safety check failed: {v.stderr}")

    win_dl = Path("/mnt/c/Users/Karoly/Downloads")
    if win_dl.exists():
        try:
            shutil.copy2(target, win_dl / "clean-night-18-custom.bin")
        except Exception:
            pass
    return target.stat().st_size


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("server: " + fmt % args + "\n")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/config":
            d = read_design()
            try:
                d["_build"] = int(BUILD_ID.read_text().strip())
            except Exception:
                d["_build"] = 0
            return self._json(d)
        if self.path == "/" or self.path == "/index.html":
            self.path = "/preview.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/values":
            try:
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n) or b"{}")
            except Exception as e:
                return self._json({"error": f"bad json: {e}"}, 400)
            try:
                cur = read_design()
                if isinstance(d.get("values"), dict):
                    cur["values"].update(d["values"])
                    write_design(cur)
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"error": str(e)[-500:]}, 500)
        if self.path != "/api/build":
            return self._json({"error": "not found"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._json({"error": f"bad json: {e}"}, 400)
        try:
            cur = read_design()
            # merge full design schema (groups merged per element)
            for k, v in d.items():
                if k.startswith("_"):
                    continue
                if k == "groups" and isinstance(v, dict):
                    for gid, gv in v.items():
                        if isinstance(gv, dict) and isinstance(
                            cur.get("groups", {}).get(gid), dict
                        ):
                            cur["groups"][gid].update(gv)
                        else:
                            cur["groups"][gid] = gv
                elif isinstance(v, dict) and isinstance(cur.get(k), dict):
                    cur[k].update(v)
                else:
                    cur[k] = v
            layout, meta = build(cur)
            write_design(cur)
            if meta.get("validationErrors"):
                return self._json({
                    "ok": False,
                    "error": f"Mi Band 5 hardware validation failed: {'; '.join(meta['validationErrors'])}",
                    "validationErrors": meta["validationErrors"],
                    "meta": meta
                }, 400)
            entry = refresh_faces_entry(layout, meta)
            try:
                size = pack_bin()
            except Exception as e:
                size = -1
                pack_err = str(e)[-500:]
            else:
                pack_err = None
            ts = int(time.time() * 1000)
            BUILD_ID.write_text(str(ts))
            out = {
                "ok": True,
                "build": ts,
                "layout": layout,
                "meta": meta,
                "binBytes": size,
            }
            if pack_err:
                out["packError"] = pack_err
            return self._json(out)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return self._json({"error": str(e)[-1000:]}, 500)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8903
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"serving {ROOT} on http://127.0.0.1:{port}/  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
