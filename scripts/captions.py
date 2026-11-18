#!/usr/bin/env python3
"""Automatic captions: speech -> words with timings -> caption cards (and an .srt file).

  python3 scripts/captions.py talk.mp4 --out captions.json [--srt talk.srt] [--lang zh] [--model small]
                               [--hint "Kopi Pagi, WhatsApp"] [--fix "Paggi=Pagi" --fix "What's up=WhatsApp"]

Then add to a project file:  "captions": {"file": "captions.json", "anim": "highlight"}
Each word lights up (or appears) when it is spoken. Uses faster-whisper (MIT), an optional dependency:
  pip install faster-whisper     (the speech model, ~0.5 GB for "small", downloads on first use)
Proper nouns are often misheard: pass them with --hint, and correct leftovers with --fix. Always read the result.
"""
import argparse, json, os, re, sys
from common import ffmpeg

CJK = re.compile(r"[　-鿿＀-￯]")
END = re.compile(r"[.!?。！？]$")

def transcribe(path, model="small", lang=None, hint=None):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("captions need faster-whisper:  pip install faster-whisper")
    os.environ.setdefault("PATH", "")
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, inf = m.transcribe(path, language=lang, word_timestamps=True, vad_filter=True, initial_prompt=hint)
    words = [(w.word, float(w.start), float(w.end)) for s in segs for w in (s.words or [])]
    return words, inf.language

SOFT = re.compile(r"[,，、;；:：]$")

def chunk(words, max_chars=None, max_dur=3.5, gap=0.45):
    """Group words into short captions. Break on sentence ends and pauses; when a caption gets too long,
    break after the last comma in it if there is one, so phrases stay together."""
    caps, cur = [], []
    def text_of(ws):
        return re.sub(r"[,，、;；:：.!?。！？]", "", "".join(x[0] for x in ws)).strip()
    for w in words:
        if cur:
            t = text_of(cur)
            limit = max_chars or (14 if CJK.search(t) else 26)
            closes = bool(END.search(w[0].strip()))          # a short last word that ends the sentence may overflow a little
            if w[1] - cur[-1][2] > gap:
                caps.append(cur); cur = []
            elif (len(text_of(cur + [w])) > limit + (3 if closes else 0)) or (w[2] - cur[0][1] > max_dur + (0.6 if closes else 0)):
                cut = max((i for i, x in enumerate(cur[:-1]) if SOFT.search(x[0].strip())), default=None)
                if cut is not None and len(text_of(cur[:cut + 1])) >= 0.25 * limit:
                    caps.append(cur[:cut + 1]); cur = cur[cut + 1:]
                else:
                    caps.append(cur); cur = []
        cur.append(w)
        if END.search(w[0].strip()):
            caps.append(cur); cur = []
    if cur:
        caps.append(cur)
    return caps

def to_caption(ws, nxt_start=None):
    """Build {from, to, lines, char_times}. Trailing punctuation is dropped from the display text."""
    text, times = "", []
    for word, s, e in ws:
        raw = word if text else word.lstrip()
        chars = [c for c in raw if not c.isspace()]
        n = max(1, len(chars))
        k = 0
        for c in raw:
            text += c
            if not c.isspace():
                times.append(s + (e - s) * k / n); k += 1
    while text and text[-1] in ",.!?，。！？、;；:：":
        text = text[:-1]
        if times:
            times.pop()
    if CJK.search(text):
        text = text.replace(",", "，").replace("?", "？").replace("!", "！")
    lines = split_lines(text.strip())
    start, end = ws[0][1], ws[-1][2] + 0.35
    if nxt_start is not None:
        end = min(end, nxt_start - 0.02)
    return {"from": round(start, 3), "to": round(max(end, start + 0.4), 3), "lines": lines, "char_times": [round(t, 3) for t in times]}

def split_lines(text, one_line=None):
    """Two balanced lines when one would be too long for a phone screen (prefer a comma or a space)."""
    cjk = bool(CJK.search(text))
    limit = one_line or (8 if cjk else 16)
    plain = re.sub(r"\s", "", text)
    if len(plain) <= limit:
        return [text]
    mid = len(text) / 2
    cands = [i + 1 for i, c in enumerate(text) if c in "，,、;；:："] + [i for i, c in enumerate(text) if c == " "]
    if not cands and cjk:
        cands = list(range(1, len(text)))
    if not cands:
        return [text]
    cut = min(cands, key=lambda i: abs(i - mid))
    a, b = text[:cut].strip(), text[cut:].strip()
    return [a, b] if a and b else [text]

def apply_fix(cap, fixes):
    """Replace misheard words; keep timings by stretching them over the new text."""
    line = " ".join(cap["lines"]) if not CJK.search("".join(cap["lines"])) else "".join(cap["lines"])
    new = line
    for f in fixes:
        if "=" not in f:
            sys.exit(f"--fix must look like wrong=right, got: {f}")
        a, b = f.split("=", 1)
        new = re.sub(re.escape(a), b, new, flags=re.I)
    if new == line:
        return cap
    old_t = cap["char_times"]; n_new = len([c for c in new if not c.isspace()])
    if not old_t or n_new == 0:
        cap["lines"] = split_lines(new); cap["char_times"] = [cap["from"]] * n_new; return cap
    cap["char_times"] = [round(old_t[min(len(old_t) - 1, int(i * len(old_t) / n_new))], 3) for i in range(n_new)]
    cap["lines"] = split_lines(new)
    return cap

def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("media"); p.add_argument("--out", required=True); p.add_argument("--srt")
    p.add_argument("--lang", help="zh, en, ms ... (default: detect)"); p.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3")
    p.add_argument("--hint", help="names and words likely in the audio, to improve spelling")
    p.add_argument("--fix", action="append", default=[], help="wrong=right, may repeat")
    p.add_argument("--max-chars", type=int)
    a = p.parse_args()
    if not os.path.exists(a.media):
        sys.exit(f"file not found: {a.media}")
    words, lang = transcribe(a.media, a.model, a.lang, a.hint)
    if not words:
        sys.exit("no speech found")
    groups = chunk(words, a.max_chars)
    caps = []
    for i, g in enumerate(groups):
        nxt = groups[i + 1][0][1] if i + 1 < len(groups) else None
        caps.append(apply_fix(to_caption(g, nxt), a.fix))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(caps, fh, ensure_ascii=False, indent=1)
    if a.srt:
        with open(a.srt, "w", encoding="utf-8") as fh:
            for i, c in enumerate(caps, 1):
                fh.write(f"{i}\n{srt_time(c['from'])} --> {srt_time(c['to'])}\n" + "\n".join(c["lines"]) + "\n\n")
    print(f"language: {lang}   {len(caps)} captions -> {a.out}" + (f" and {a.srt}" if a.srt else ""))
    for c in caps:
        print(f"  {c['from']:6.2f}-{c['to']:6.2f}  " + " / ".join(c["lines"]))
    print("Check the spelling of names before publishing.")

if __name__ == "__main__":
    main()
