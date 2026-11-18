#!/usr/bin/env python3
"""Check a finished video without watching it: size, loudness per second, frozen picture, contact sheet.

  python3 scripts/check.py video.mp4 [--expect 1080x1920] [--sheet sheet.jpg] [--at 39.7 --at 50.3]

--at T   print the loudness just before and at T, to confirm a sound effect really landed there.
Exit code 1 if a check fails. This is a measurement, not a listen: still play the result before publishing.
"""
import argparse, re, subprocess, sys
from common import ffmpeg, info, run

def loudness(path, step=1.0):
    """RMS level (dB) for each `step` seconds."""
    n = int(48000 * step)
    r = subprocess.run([ffmpeg(), "-v", "error", "-nostdin", "-i", path, "-vn", "-af",
                        f"aresample=48000,asetnsamples={n},astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
                        "-f", "null", "-"], capture_output=True, text=True)
    vals = []
    for m in re.finditer(r"RMS_level=(-?[\d.]+|-inf)", r.stdout):
        vals.append(-99.0 if m[1] == "-inf" else float(m[1]))
    return vals

def freezes(path, min_len=1.0):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-nostdin", "-i", path, "-an", "-vf", f"freezedetect=n=-60dB:d={min_len}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    durs = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", r.stderr)]
    return list(zip(starts, durs))

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video"); p.add_argument("--expect"); p.add_argument("--sheet"); p.add_argument("--at", type=float, action="append", default=[]); p.add_argument("--silent-ok", action="store_true", help="a clip with no audio track is fine (e.g. a title used as a shot)")
    a = p.parse_args()
    ok = True
    i = info(a.video)
    print(f"{a.video}\n  {i['width']}x{i['height']}  {i['fps']:g} fps  {i['duration']:.2f}s  audio: {'yes' if i['has_audio'] else 'NO'}")
    if a.expect and a.expect.lower() != f"{i['width']}x{i['height']}":
        print(f"  FAIL size: expected {a.expect}"); ok = False
    if i["has_audio"]:
        v = loudness(a.video)
        print("  loudness per second (dB): " + " ".join(f"{x:.0f}" for x in v))
        quiet = [t for t, x in enumerate(v[:-1]) if x < -45]
        if quiet:
            print(f"  WARN near-silent seconds: {quiet}")
        fine = loudness(a.video, 0.25)
        for t in a.at:
            k = int(t / 0.25)
            before = fine[max(0, k - 2)] if fine else -99; at = max(fine[k:k + 3]) if fine[k:k + 3] else -99
            verdict = "louder" if at > before + 1.5 else "NOT clearly louder"
            print(f"  cue at {t:.2f}s: {before:.0f} dB before -> {at:.0f} dB  ({verdict})")
    elif a.silent_ok:
        print("  no audio track (allowed)")
    else:
        print("  FAIL no audio track"); ok = False
    fz = freezes(a.video)
    for s, d in fz:
        print(f"  WARN picture frozen {d:.1f}s from {s:.1f}s")
    if a.sheet:
        n = 12; step = max(i["duration"] / n, 0.1)
        run(["-i", a.video, "-vf", f"fps=1/{step:.3f},scale=-2:320,tile={n}x1", "-frames:v", "1", a.sheet])
        print("  contact sheet:", a.sheet)
    print("  result:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
