"""Animated text cards, rendered frame by frame with Pillow into transparent PNGs (no extra dependencies).

Animations
  typewriter  characters appear one by one, as if typed
  words       words pop in one after another
  highlight   the whole line is visible; words turn the accent colour in order (karaoke style)
  pop         the whole card bounces in
The reveal always finishes before the card ends, so text is never cut off mid-way.
"""
import math, os
from PIL import Image, ImageChops, ImageColor, ImageDraw
from make_card import _load, layout

ANIMS = ["typewriter", "words", "highlight", "pop"]
_fonts = {}

def _font(path, sz, idx):
    key = (path, int(sz), idx)
    if key not in _fonts:
        _fonts[key] = _load(path, int(sz), idx)
    return _fonts[key]

def _rgba(c, a=1.0):
    r, g, b = ImageColor.getrgb(c)[:3]
    return (r, g, b, int(255 * max(0.0, min(1.0, a))))

def _put(d, it, a=1.0, scale=1.0, cx=None, cy=None, fill=None):
    """Draw one character, optionally scaled around (cx, cy)."""
    sz = it["sz"] * scale
    f = _font(it["path"], sz, it["idx"])
    x, y = it["x"], it["y"]
    if scale != 1.0:
        x = cx + (x - cx) * scale
        y = cy + (y - cy) * scale
    d.text((x + 2, y + 3), it["ch"], font=f, fill=(0, 0, 0, int(170 * a)))
    d.text((x, y), it["ch"], font=f, fill=_rgba(fill or it["fill"], a))

def reveal_time(anim, dur, n_chars, n_words, reveal=None):
    """Seconds the reveal takes; always leaves time to read the finished text."""
    natural = {"typewriter": 0.07 * n_chars, "words": 0.22 * n_words, "highlight": 0.30 * n_words, "pop": 0.3}[anim]
    r = natural if reveal is None else float(reveal)
    return max(0.2, min(r, dur - 0.7 if dur > 1.4 else dur * 0.5))

def render(outdir, lines, dur, fps=30, anim="typewriter", size=(1080, 1920), reveal=None, accent="#B0F03E", char_times=None, **layout_kw):
    """Write frames %05d.png for a card lasting `dur` seconds. Returns the number of frames.
    char_times: optional start time (seconds from the card start) for every non-space character, e.g. from speech
    recognition; words then appear or light up exactly when they are spoken."""
    if anim not in ANIMS:
        raise ValueError(f"unknown text animation '{anim}'. Use one of {ANIMS}")
    os.makedirs(outdir, exist_ok=True)
    items = layout(lines, size, accent=accent, **layout_kw)
    shown = [it for it in items if it["word"] >= 0]
    n_words = max([it["word"] for it in shown], default=-1) + 1
    R = reveal_time(anim, dur, len(shown), n_words, reveal)
    words = {}
    for it in shown:
        words.setdefault(it["word"], []).append(it)
    wt = None
    if char_times is not None:
        if len(char_times) != len(shown):
            raise ValueError(f"char_times has {len(char_times)} entries but the text has {len(shown)} non-space characters")
        wt = {}
        for it, ct in zip(shown, char_times):
            wt[it["word"]] = min(wt.get(it["word"], ct), ct)
        for it, ct in zip(shown, char_times):
            it["t"] = ct
    start_of = (lambda k: wt[k]) if wt else (lambda k: R * k / max(1, n_words))
    centre = {k: ((v[0]["x"] + v[-1]["x"] + v[-1]["w"]) / 2, v[0]["y"] + v[0]["sz"] * 0.55) for k, v in words.items()}
    bx = (min(it["x"] for it in shown) + max(it["x"] + it["w"] for it in shown)) / 2 if shown else size[0] / 2
    by = (min(it["y"] for it in shown) + max(it["y"] + it["sz"] for it in shown)) / 2 if shown else size[1] / 2
    n = max(1, int(round(dur * fps)))
    for f in range(n):
        t = f / fps
        im = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if anim == "typewriter":
            if wt:
                for it in shown:
                    if t >= it["t"]:
                        _put(d, it)
            else:
                count = min(len(shown), math.ceil(min(1.0, t / R) * len(shown)))
                for it in shown[:count]:
                    _put(d, it)
        elif anim == "words":
            for k, chars in words.items():
                t0 = start_of(k)
                if t < t0:
                    continue
                p = min(1.0, (t - t0) / 0.14)
                for it in chars:
                    _put(d, it, a=min(1.0, p * 1.6), scale=1 + 0.3 * (1 - p), cx=centre[k][0], cy=centre[k][1])
        elif anim == "highlight":
            a = min(1.0, t / 0.2)
            for k, chars in words.items():
                lit = t >= start_of(k)
                for it in chars:
                    _put(d, it, a=a, fill=accent if lit else "#FFFFFF")
        else:  # pop
            s = 0.6 + 0.5 * (t / 0.18) if t < 0.18 else (1.1 - 0.1 * ((t - 0.18) / 0.12) if t < 0.30 else 1.0)
            for it in shown:
                _put(d, it, a=min(1.0, t / 0.12), scale=s, cx=bx, cy=by)
        out_a = min(1.0, (dur - t) / 0.25)                       # fade the whole card out at the end
        if out_a < 1.0:
            im.putalpha(ImageChops.multiply(im.getchannel("A"), Image.new("L", size, int(255 * max(0.0, out_a)))))
        im.save(os.path.join(outdir, f"{f:05d}.png"), compress_level=1)
    return n
