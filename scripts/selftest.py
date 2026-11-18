#!/usr/bin/env python3
"""End-to-end self test: make demo media, build the demo project, verify the result.  python3 scripts/selftest.py"""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
from common import info
from check import loudness
subprocess.run([sys.executable, os.path.join(root, "examples", "make_demo_assets.py")], check=True)
subprocess.run([sys.executable, os.path.join(here, "build.py"), os.path.join(root, "examples", "demo_project.json")], check=True)
out = os.path.join(root, "examples", "out", "demo_9x16.mp4")
i = info(out); v = loudness(out, 0.25)
checks = [("size is 1080x1920", (i["width"], i["height"]) == (1080, 1920)),
          ("length is 8.0s", abs(i["duration"] - 8.0) < 0.15),
          ("has audio", i["has_audio"]),
          ("boom at 3.0s is louder than the music before it", max(v[12:15]) > v[10] + 3),
          ("chime at 5.5s is louder than the music before it", max(v[22:25]) > v[20] + 3)]
subprocess.run([sys.executable, os.path.join(root, "examples", "ad_example", "make_placeholder_assets.py")], check=True, stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, os.path.join(here, "build.py"), os.path.join(root, "examples", "text_project.json")], check=True, stdout=subprocess.DEVNULL)
ad = subprocess.run([sys.executable, os.path.join(here, "ad.py"), "build", os.path.join(root, "examples", "ad_example")], capture_output=True, text=True)
ai = info(os.path.join(root, "examples", "ad_example", "out", "kopi_pagi_cold_brew_animatic.mp4")) if ad.returncode == 0 else {"duration": 0}
ti = info(os.path.join(root, "examples", "out", "text_9x16.mp4"))
checks += [("animated-text example builds (12.0s)", abs(ti["duration"] - 12.0) < 0.15),
           ("one-sentence ad example builds an animatic (14.2s)", abs(ai["duration"] - 14.2) < 0.15)]
import shutil, importlib.util, json, tempfile
if importlib.util.find_spec("faster_whisper") and shutil.which("say"):      # optional: captions (macOS voice for the test audio)
    td = tempfile.mkdtemp()
    subprocess.run(["say", "-v", "Samantha", "-o", os.path.join(td, "v.aiff"), "Kopi Pagi is ready in ten seconds. WhatsApp us to order."], check=True)
    r = subprocess.run([sys.executable, os.path.join(here, "captions.py"), os.path.join(td, "v.aiff"), "--out", os.path.join(td, "c.json"),
                        "--lang", "en", "--hint", "Kopi Pagi, WhatsApp"], capture_output=True, text=True)
    caps = json.load(open(os.path.join(td, "c.json"))) if r.returncode == 0 else []
    text = " ".join(" ".join(c["lines"]) for c in caps)
    checks += [("captions: speech recognised with word timings", bool(caps) and all(len("".join(c["lines"]).replace(" ", "")) == len(c["char_times"]) for c in caps)),
               ("captions: names spelled from --hint (Kopi Pagi, WhatsApp)", "Kopi Pagi" in text and "WhatsApp" in text)]
    shutil.rmtree(td, ignore_errors=True)
else:
    print("SKIP  captions (needs `pip install faster-whisper`; the test voice needs macOS `say`)")
if shutil.which("npx") and (os.environ.get("FFPROBE") or shutil.which("ffprobe")):   # optional: HyperFrames titles
    r = subprocess.run([sys.executable, os.path.join(here, "build.py"), os.path.join(root, "examples", "motion_project.json")], capture_output=True, text=True)
    mi = info(os.path.join(root, "examples", "out", "motion_9x16.mp4")) if r.returncode == 0 else {"duration": 0, "width": 0}
    checks += [("motion: brand intro/outro rendered with HyperFrames and built (8.2s)", abs(mi["duration"] - 8.2) < 0.15 and mi["width"] == 1080)]
else:
    print("SKIP  motion titles (needs Node.js 22+ and ffprobe)")
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name)
sys.exit(0 if all(ok for _, ok in checks) else 1)
