#!/usr/bin/env python3
"""Generate copyright-free practice media with ffmpeg (test patterns, a synth music bed, two effects).

  python3 examples/make_demo_assets.py        -> examples/demo_assets/
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from common import run

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_assets")
os.makedirs(os.path.join(out, "sfx"), exist_ok=True)
V = ["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p"]
for name, src in [("clip_a", "testsrc2=s=1920x1080:r=30"), ("clip_b", "mandelbrot=s=1920x1080:r=30"), ("clip_c", "gradients=s=1920x1080:r=30:speed=0.05")]:
    run(["-f", "lavfi", "-t", "8", "-i", src] + V + [os.path.join(out, name + ".mp4")])
run(["-f", "lavfi", "-t", "30", "-i", "sine=f=110:r=48000", "-f", "lavfi", "-t", "30", "-i", "sine=f=165:r=48000", "-f", "lavfi", "-t", "30", "-i", "sine=f=220:r=48000",
     "-filter_complex", "[0][1][2]amix=inputs=3:normalize=0,tremolo=f=2:d=0.6,volume=0.12,pan=stereo|c0=c0|c1=c0", os.path.join(out, "music.mp3")])
run(["-f", "lavfi", "-t", "2", "-i", "anoisesrc=c=brown:r=48000:a=0.9",
     "-af", "afade=t=in:d=0.05,afade=t=out:st=0.3:d=1.7,pan=stereo|c0=c0|c1=c0", os.path.join(out, "sfx", "boom.mp3")])
run(["-f", "lavfi", "-t", "1.2", "-i", "sine=f=660:r=48000",
     "-af", "vibrato=f=9:d=0.6,afade=t=out:st=0.2:d=1.0,volume=0.8,pan=stereo|c0=c0|c1=c0", os.path.join(out, "sfx", "chime.mp3")])
print("demo assets in", out)
