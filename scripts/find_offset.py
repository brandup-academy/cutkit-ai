#!/usr/bin/env python3
"""Find the time offset between a screen recording and its original render by comparing tiny frames.

  python3 scripts/find_offset.py recording.mov original.mp4
prints: recording frame i matches original frame i+LAG  (30 fps). Needs numpy.
"""
import argparse, subprocess, tempfile, os
import numpy as np
from common import ffmpeg

def frames(ff, path):
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as t: tmp = t.name
    subprocess.run([ff, "-v", "error", "-y", "-i", path, "-vf", "fps=30,scale=36:64,format=gray", "-f", "rawvideo", tmp], check=True)
    x = np.fromfile(tmp, dtype=np.uint8).reshape(-1, 64 * 36).astype(float); os.remove(tmp); return x

p = argparse.ArgumentParser(); p.add_argument("rec"); p.add_argument("orig")
a = p.parse_args(); r, o = frames(ffmpeg(), a.rec), frames(ffmpeg(), a.orig)
best = None
for lag in range(-60, 61):
    idx = [i for i in range(0, len(r), 3) if 0 <= i + lag < len(o)]
    e = np.mean([np.abs(r[i] - o[i + lag]).mean() for i in idx])
    if best is None or e < best[0]: best = (e, lag)
print(f"error {best[0]:.2f}; recording frame i matches original frame i+{best[1]}  ({best[1]/30:.3f}s)")
