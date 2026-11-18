"""Shared helpers: locate ffmpeg, read media info, find a usable font."""
import os, re, shutil, subprocess, sys

# Windows consoles and pipes often default to a legacy code page; print Chinese text safely everywhere.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def ffmpeg():
    p = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found. Install ffmpeg, or set FFMPEG=/path/to/ffmpeg, or `pip install imageio-ffmpeg`.")

def run(args):
    """Run ffmpeg quietly; raise with the error text if it fails."""
    r = subprocess.run([ffmpeg(), "-y", "-v", "error", "-nostdin"] + [str(a) for a in args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + r.stderr.strip()[-2000:])
    return r

def info(path):
    """Return dict(duration, width, height, fps, has_audio) parsed from `ffmpeg -i`."""
    if not os.path.exists(path):
        sys.exit(f"file not found: {path}")
    err = subprocess.run([ffmpeg(), "-hide_banner", "-nostdin", "-i", str(path)], capture_output=True, text=True).stderr
    d = {"duration": 0.0, "width": 0, "height": 0, "fps": 0.0, "has_audio": "Audio:" in err}
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if m:
        d["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    if m:
        d["width"], d["height"] = int(m[1]), int(m[2])
    m = re.search(r"([\d.]+) fps", err)
    if m:
        d["fps"] = float(m[1])
    return d

_LATIN = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
          "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
_CJK = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Supplemental/Songti.ttc",
        "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"]

def find_font(cjk=False):
    """Return the first system font that exists, or None (Pillow's built-in font is used then)."""
    for p in (_CJK if cjk else _LATIN):
        if os.path.exists(p):
            return p
    return None
