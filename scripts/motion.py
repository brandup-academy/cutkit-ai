#!/usr/bin/env python3
"""Animated brand title / end card rendered with HyperFrames (optional, needs Node.js 22+ and Chrome).

  python3 scripts/motion.py out.mp4 --title "BrandUp Academy" [--kicker "AI VIDEO LAB"] [--subtitle "Learn AI. Create better content."]
                            [--size 9:16] [--dur 3] [--accent "#B0F03E"] [--bg "#0A0B0D"] [--font "Inter, Arial, sans-serif"]

The result is an ordinary MP4: use it as a shot in a project file ({"src": "intro.mp4", "dur": 3}).
Uses HyperFrames (Apache-2.0) via `npx hyperframes@<pinned version>`; the first run downloads it.
The template loads GSAP from a CDN, so rendering needs an internet connection. Telemetry: run
`npx hyperframes telemetry disable` once if you do not want usage statistics sent to HeyGen.
"""
import argparse, html, json, os, shutil, subprocess, sys, tempfile
from common import ffmpeg

HF_VERSION = "0.9.56"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = {"9:16": (1080, 1920, "portrait"), "16:9": (1920, 1080, "landscape"), "1:1": (1080, 1080, "square")}

def _expose(src, bin_dir, name):
    """Make `src` callable as `name` from bin_dir: a symlink where allowed, a copy otherwise (Windows needs .exe)."""
    dst = os.path.join(bin_dir, name + (".exe" if os.name == "nt" else ""))
    try:
        if os.name == "nt":
            raise OSError("copy on Windows")
        os.symlink(src, dst)
    except OSError:
        shutil.copy2(src, dst)

def render_title(out, title, kicker="", subtitle="", size="9:16", dur=3.0, accent="#B0F03E", bg="#0A0B0D", ink="#FFFFFF",
                 font="Inter, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif", template="brand_title"):
    npx = shutil.which("npx")                                          # npx.cmd on Windows
    if not npx:
        sys.exit("motion titles need Node.js 22+ (npx not found). Install from https://nodejs.org")
    if size not in SIZES:
        sys.exit(f"--size must be one of {list(SIZES)}")
    W, H, res = SIZES[size]
    if dur < 1.5:
        sys.exit("--dur must be at least 1.5 seconds so the title can finish animating")
    src = os.path.join(ROOT, "motion", template, "index.html")
    with open(src, encoding="utf-8") as fh:
        page = fh.read()
    margin = round(W * 180 / 1080)
    longest = max((len(w) for w in title.split()), default=1)        # size so the longest word fits on one line
    title_size = int(min(W * 0.13, H * 0.12, (W - 2 * margin) / (longest * 0.62)))
    # letters animate one by one, but a word never breaks across lines
    spans = " ".join('<span class="w">' + "".join(f'<span class="c">{html.escape(c)}</span>' for c in word) + "</span>" for word in title.split())
    vals = {"W": W, "H": H, "RESOLUTION": res, "DUR": dur, "BG": bg, "INK": ink, "ACCENT": accent, "FONT": font, "MARGIN": margin,
            "GLOW": int(W * 0.9), "GLOW_HALF": int(W * 0.45), "KICK_SIZE": int(W * 0.03), "TITLE_SIZE": title_size,
            "SUB_SIZE": int(W * 0.04), "BAR_W": int(W * 0.18), "KICKER": html.escape(kicker), "TITLE_SPANS": spans,
            "SUBTITLE": html.escape(subtitle)}
    for k, v in vals.items():
        page = page.replace("{{" + k + "}}", str(v))
    tmp = tempfile.mkdtemp(prefix="motion_")
    try:
        with open(os.path.join(tmp, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        with open(os.path.join(tmp, "hyperframes.json"), "w") as fh:
            json.dump({"media": {"autoProxy": True}}, fh)
        env = dict(os.environ)
        ff = ffmpeg()
        bin_dir = tempfile.mkdtemp(prefix="motion_bin_")                 # outside the project folder
        _expose(ff, bin_dir, "ffmpeg")                                  # HyperFrames looks for ffmpeg and ffprobe on PATH
        probe = os.environ.get("FFPROBE") or shutil.which("ffprobe")
        if not probe:
            sys.exit("motion titles need ffprobe, which comes with a full FFmpeg install (macOS: `brew install ffmpeg`, "
                     "Windows: `winget install ffmpeg`), or set FFPROBE=/path/to/ffprobe")
        _expose(probe, bin_dir, "ffprobe")
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        out_abs = os.path.abspath(out)
        r = subprocess.run([npx, "--yes", f"hyperframes@{HF_VERSION}", "render", "-o", out_abs, "--fps", "30", "--quality", "high", "--quiet"],
                           cwd=tmp, env=env, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out_abs):
            sys.exit("HyperFrames render failed:\n" + (r.stderr or r.stdout)[-2500:])
        return out_abs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if 'bin_dir' in locals():
            shutil.rmtree(bin_dir, ignore_errors=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out"); p.add_argument("--title", required=True); p.add_argument("--kicker", default=""); p.add_argument("--subtitle", default="")
    p.add_argument("--size", default="9:16"); p.add_argument("--dur", type=float, default=3.0)
    p.add_argument("--accent", default="#B0F03E"); p.add_argument("--bg", default="#0A0B0D"); p.add_argument("--ink", default="#FFFFFF")
    p.add_argument("--font", default="Inter, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif")
    a = p.parse_args()
    print("wrote", render_title(a.out, a.title, a.kicker, a.subtitle, a.size, a.dur, a.accent, a.bg, a.ink, a.font))
