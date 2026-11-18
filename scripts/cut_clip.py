#!/usr/bin/env python3
"""Cut a short silent 1280x720 clip to upload to a video-to-sound-effect tool.

  python3 scripts/cut_clip.py film.mp4 17.2 clip.mp4 [--dur 6]
"""
import argparse
from common import run

def cut_clip(src, start, out, dur=6.0):
    run(["-ss", start, "-t", dur, "-i", src, "-an",
         "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
         "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", out])
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src"); p.add_argument("start", type=float); p.add_argument("out"); p.add_argument("--dur", type=float, default=6.0)
    a = p.parse_args()
    print("wrote", cut_clip(a.src, a.start, a.out, a.dur))
