#!/usr/bin/env python3
"""Mix sound-effect cues into a video's music bed, ducking the music while each effect plays.

  python3 scripts/mix_sfx.py --video base.mp4 --out out.mp4 --cues cues.json [--sfx-dir DIR] [--duck 0.5] [--gain 1.4]

cues.json: [{"file": "roar.mp3", "at": 39.7, "start": 0.0, "end": 6.0, "gain": 1.0}, ...]
  file  audio file (relative to --sfx-dir)        at    position in the video, seconds
  start/end  part of the audio file to use (default: the whole file)     gain  optional multiplier
The picture is copied, not re-encoded.
"""
import argparse, json, os, sys
from common import run, info

def mix(video, out, cues, sfx_dir=".", duck=0.5, gain=1.4):
    if not cues:
        sys.exit("no cues to mix")
    vi = info(video)
    ins = ["-i", video]
    bed = "[0:a]"
    if not vi["has_audio"]:                       # silent picture: mix over silence
        ins += ["-f", "lavfi", "-t", vi["duration"], "-i", "anullsrc=r=48000:cl=stereo"]
        bed = "[1:a]"
    first = len(ins) // 2 if vi["has_audio"] else 2
    fc, labels, windows = [], [], []
    for i, c in enumerate(cues):
        path = os.path.join(sfx_dir, c["file"])
        full = info(path)["duration"]
        s = float(c.get("start", 0.0)); e = float(c.get("end", full)); t = float(c["at"])
        if not 0 <= s < e:
            sys.exit(f"cue {i} ({c['file']}): need 0 <= start < end")
        if t >= vi["duration"]:
            sys.exit(f"cue {i} ({c['file']}): at={t} is past the end of the video ({vi['duration']:.2f}s)")
        d = e - s
        fi, fo = min(0.15, d / 3), min(0.4, d / 2)
        ms = int(round(t * 1000))
        ins += ["-i", path]
        fc.append(f"[{first + i}:a]atrim={s}:{e},asetpts=PTS-STARTPTS,aresample=48000,volume={gain * float(c.get('gain', 1.0))},"
                  f"afade=t=in:d={fi:.3f},afade=t=out:st={d - fo:.3f}:d={fo:.3f},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
        windows.append(f"between(t,{max(0, t - 0.15):.2f},{t + d + 0.15:.2f})")
    fc.append(f"{bed}aresample=48000,volume='if(gt({'+'.join(windows)},0),{duck},1)':eval=frame[bed]")
    fc.append(f"[bed]{''.join(labels)}amix=inputs={len(cues) + 1}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    run(ins + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--video", required=True); p.add_argument("--out", required=True); p.add_argument("--cues", required=True)
    p.add_argument("--sfx-dir", default="."); p.add_argument("--duck", type=float, default=0.5); p.add_argument("--gain", type=float, default=1.4)
    a = p.parse_args()
    with open(a.cues, encoding="utf-8") as fh:
        cues = json.load(fh)
    print("wrote", mix(a.video, a.out, cues, a.sfx_dir, a.duck, a.gain))
