#!/usr/bin/env python3
"""Fill this example with placeholder media so `ad.py build` can run without spending credits.
Shots b1-b2 get video, b3-b5 get stills, to show the animatic stage.  Run make_demo_assets.py first."""
import os, shutil, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(os.path.dirname(here))
sys.path.insert(0, os.path.join(root, "scripts"))
from common import run
demo = os.path.join(root, "examples", "demo_assets"); a = os.path.join(here, "assets"); os.makedirs(a, exist_ok=True)
shutil.copy(os.path.join(demo, "clip_a.mp4"), os.path.join(a, "b1.mp4"))
shutil.copy(os.path.join(demo, "clip_b.mp4"), os.path.join(a, "b2.mp4"))
for i, (clip, t) in enumerate([("clip_c", 1), ("clip_b", 5), ("clip_c", 6)], 3):
    run(["-ss", t, "-i", os.path.join(demo, clip + ".mp4"), "-frames:v", "1", os.path.join(a, f"b{i}.jpg")])
shutil.copy(os.path.join(demo, "music.mp3"), os.path.join(a, "music.mp3"))
shutil.copy(os.path.join(demo, "sfx", "boom.mp3"), os.path.join(a, "b1_sfx.mp3"))
shutil.copy(os.path.join(demo, "sfx", "chime.mp3"), os.path.join(a, "b5_sfx.mp3"))
print("placeholder assets in", a)
