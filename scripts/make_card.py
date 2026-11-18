#!/usr/bin/env python3
"""Draw a transparent title / subtitle card PNG whose text stays inside the safe side margins.

  python3 scripts/make_card.py card.png "YOU CAN [[PLAY IT]]" "RIGHT NOW." [--size 1080x1920] [--font F] [--cjk-font F]

[[double brackets]] colour a phrase with the accent colour. Text shrinks until it fits the safe width
(a 180 px margin on each side of a 1080-wide frame, scaled for other widths). Needs Pillow.
"""
import argparse, re, sys
from PIL import Image, ImageDraw, ImageFont
from common import find_font

_CJK_RE = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")

def _load(path, size, index=0):
    if path:
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)          # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()

def layout(lines, size=(1080, 1920), font=None, cjk_font=None, font_index=0, font_size=72,
           y=None, accent="#B0F03E", color="#FFFFFF", margin=None, spacing=8):
    """Place every character. Returns a list of dicts: ch, x, y, path, idx, sz, fill, word, line, w.
    `word` numbers the words in reading order (-1 for spaces); each CJK character counts as a word."""
    W, H = size
    margin = round(W * 180 / 1080) if margin is None else margin
    max_w = W - 2 * margin
    font = font or find_font()
    cjk_font = cjk_font or find_font(cjk=True) or font
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    y = round(H * 0.61) if y is None else y
    items, wid = [], -1
    for li, line in enumerate(lines):
        is_cjk = bool(_CJK_RE.search(line))
        path, idx = (cjk_font, 0) if is_cjk else (font, font_index)
        parts = [(t, bool(i % 2)) for i, t in enumerate(re.split(r"\[\[|\]\]", line)) if t]
        sz, sp = font_size, float(spacing)
        while True:
            f = _load(path, sz, idx)
            w = sum(d.textlength(c, font=f) + sp for t, _ in parts for c in t) - sp
            if w <= max_w or sz <= 18:
                break
            sz -= 2
            sp = max(2.0, sp - 0.3)
        x = (W - w) / 2
        is_open = False
        for t, acc in parts:
            for ch in t:
                cw = d.textlength(ch, font=f)
                if ch.isspace():
                    word, is_open = -1, False
                elif _CJK_RE.match(ch):
                    wid += 1; word, is_open = wid, False
                else:
                    if not is_open:
                        wid += 1; is_open = True
                    word = wid
                items.append(dict(ch=ch, x=x, y=y, path=path, idx=idx, sz=sz, fill=accent if acc else color, word=word, line=li, w=cw))
                x += cw + sp
        y += sz + round(sz * 0.42)
    return items

def draw_card(out, lines, size=(1080, 1920), font=None, cjk_font=None, font_index=0, font_size=72,
              y=None, accent="#B0F03E", color="#FFFFFF", margin=None, spacing=8, shadow=True):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for it in layout(lines, size, font, cjk_font, font_index, font_size, y, accent, color, margin, spacing):
        f = _load(it["path"], it["sz"], it["idx"])
        if shadow:
            d.text((it["x"] + 2, it["y"] + 3), it["ch"], font=f, fill=(0, 0, 0, 170))
        d.text((it["x"], it["y"]), it["ch"], font=f, fill=it["fill"])
    im.save(out)
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out"); p.add_argument("lines", nargs="+")
    p.add_argument("--size", default="1080x1920"); p.add_argument("--font"); p.add_argument("--cjk-font")
    p.add_argument("--font-index", type=int, default=0); p.add_argument("--font-size", type=int, default=72)
    p.add_argument("--y", type=int); p.add_argument("--accent", default="#B0F03E"); p.add_argument("--margin", type=int)
    a = p.parse_args()
    try:
        W, H = (int(v) for v in a.size.lower().split("x"))
    except ValueError:
        sys.exit("--size must look like 1080x1920")
    draw_card(a.out, a.lines, (W, H), a.font, a.cjk_font, a.font_index, a.font_size, a.y, a.accent, margin=a.margin)
    print("wrote", a.out)

if __name__ == "__main__":
    main()
