#!/usr/bin/env python3
"""Build a whole promo video from one project file: shots + effects -> transitions -> text cards -> music -> sound effects.

  python3 scripts/build.py project.json [--keep-temp]

See docs/PROJECT_FORMAT.md for every option. Lines starting with // are allowed in the project file.
"""
import argparse, json, os, re, shutil, sys, tempfile
from common import run, info
from make_card import draw_card
from mix_sfx import mix
import anim_text

SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "4:5": (1080, 1350), "1:1": (1080, 1080)}

# picture effects: name -> ffmpeg filter ({W} {H} {d} are filled in)
FX = {
    "grade":    "eq=contrast=1.08:saturation=1.15:gamma=0.97",
    "warm":     "colorbalance=rs=0.08:gs=0.02:bs=-0.08",
    "cool":     "colorbalance=rs=-0.08:bs=0.10",
    "bw":       "hue=s=0",
    "vignette": "vignette=angle=PI/4.6",
    "grain":    "noise=alls=7:allf=t",
    "sharpen":  "unsharp=5:5:0.6",
    "glitch":   "rgbashift=rh=-10:bh=10:rv=4:bv=-4",
    "mirror":   "hflip",
    "flash":    "fade=t=in:st=0:d=0.25:color=white",
    "dip":      "fade=t=in:st=0:d=0.3,fade=t=out:st={dm}:d=0.3",
    "shake":    "scale=trunc({W}*1.06/2)*2:trunc({H}*1.06/2)*2,crop={W}:{H}:(iw-{W})/2*(1+sin(t*41)):(ih-{H})/2*(1+cos(t*53))",
    "reverse":  "reverse",
}
TRANSITIONS = ["fade", "fadeblack", "fadewhite", "wipeleft", "wiperight", "wipeup", "wipedown", "slideleft", "slideright",
               "slideup", "slidedown", "circleopen", "circleclose", "dissolve", "pixelize", "radial", "zoomin", "smoothleft", "smoothright"]

def load(path):
    with open(path, encoding="utf-8") as fh:
        text = re.sub(r"^\s*//.*$", "", fh.read(), flags=re.M)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"{path}: not valid JSON ({e})")

def fx_chain(names, W, H, d):
    out = []
    for n in names:
        if n not in FX:
            sys.exit(f"unknown effect '{n}'. Available: {', '.join(sorted(FX))}")
        out.append(FX[n].format(W=W, H=H, d=d, dm=max(0, d - 0.3)))
    return out

def build(project_path, keep_temp=False):
    pj = load(project_path)
    base = os.path.dirname(os.path.abspath(project_path))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    size = pj.get("size", "9:16")
    if isinstance(size, str):
        size = SIZES.get(size) or sys.exit(f"unknown size '{size}'. Use one of {list(SIZES)} or [width, height]")
    W, H = size; fps = pj.get("fps", 30)
    shots = pj.get("shots") or sys.exit("project needs at least one shot")
    out = P(pj.get("out", "out.mp4")); os.makedirs(os.path.dirname(out), exist_ok=True)
    look = pj.get("look", [])
    tmp = tempfile.mkdtemp(prefix="promo_")
    try:
        # 1. every shot becomes a same-size, same-fps silent segment (crop, speed, push-in, effects)
        segs = []
        for i, s in enumerate(shots):
            d = float(s["dur"]); z = float(s.get("zoom", 0.07)); cx = float(s.get("cx", 0.5)); cy = float(s.get("cy", 0.5))
            speed = float(s.get("speed", 1.0))
            vf = []
            if speed != 1.0:
                vf.append(f"setpts=PTS/{speed}")
            vf.append(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})*{cy}")
            if z:
                vf.append(f"scale=w='trunc({W}*(1+{z}*t/{d})/2)*2':h='trunc({H}*(1+{z}*t/{d})/2)*2':eval=frame:flags=bilinear,crop={W}:{H}")
            vf += fx_chain(list(s.get("fx", [])) + list(look), W, H, d)
            vf.append(f"fps={fps},setsar=1,format=yuv420p")
            seg = os.path.join(tmp, f"s{i:03d}.mp4")
            if "motion" in s:                                       # animated brand title rendered with HyperFrames
                from motion import render_title
                mo = dict(s["motion"]); mclip = os.path.join(tmp, f"motion{i}.mp4")
                msize = next((k for k, v in SIZES.items() if v == (W, H)), "9:16")
                render_title(mclip, mo.pop("title"), mo.pop("kicker", ""), mo.pop("subtitle", ""), msize, d,
                             mo.pop("accent", pj.get("accent", "#B0F03E")), **mo)
                src = ["-i", mclip]
            elif "image" in s:
                src = ["-loop", "1", "-t", d, "-i", P(s["image"])]
            else:
                si = info(P(s["src"])); st = float(s.get("start", 0)); need = d * speed
                if st + need > si["duration"] + 0.05:
                    sys.exit(f"shot {i}: {s['src']} is {si['duration']:.2f}s long, cannot take {need:.2f}s from {st}s")
                src = ["-ss", st, "-t", need, "-i", P(s["src"])]
            run(src + ["-an", "-vf", ",".join(vf), "-t", d, "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-r", fps, seg])
            segs.append(seg)
            print(f"  shot {i + 1}/{len(shots)}  {d:.2f}s" + (f"  fx: {', '.join(s['fx'])}" if s.get("fx") else ""))
        # quality warnings (they do not stop the build)
        warn = []
        for i, s_ in enumerate(shots):
            if float(s_["dur"]) < 0.8:
                warn.append(f"shot {i + 1} is {s_['dur']}s: shorter than 0.8s reads as a flash")
        # 2. join with cuts or transitions
        ins, fc = [], []
        for i, seg in enumerate(segs):
            ins += ["-i", seg]
            fc.append(f"[{i}:v]fps={fps},settb=AVTB[n{i}]")
        cur, total = "n0", float(shots[0]["dur"])
        for i in range(1, len(segs)):
            d = float(shots[i]["dur"]); tr = shots[i].get("transition")
            if tr:
                tr = {"type": tr} if isinstance(tr, str) else tr
                kind = tr.get("type", "fade"); td = float(tr.get("dur", 0.4))
                if kind not in TRANSITIONS:
                    sys.exit(f"unknown transition '{kind}'. Available: {', '.join(TRANSITIONS)}")
                if td >= min(d, float(shots[i - 1]["dur"])):
                    sys.exit(f"shot {i}: transition ({td}s) must be shorter than both shots")
                fc.append(f"[{cur}][n{i}]xfade=transition={kind}:duration={td}:offset={total - td:.3f},fps={fps},settb=AVTB[j{i}]")
                total += d - td
            else:
                fc.append(f"[{cur}][n{i}]concat=n=2:v=1:a=0,fps={fps},settb=AVTB[j{i}]")
                total += d
            cur = f"j{i}"
        # 3. text cards
        prev, n = cur, len(segs)
        cards = list(pj.get("cards", []))
        cap = pj.get("captions")
        if cap:                                                      # speech captions from scripts/captions.py
            with open(P(cap["file"]), encoding="utf-8") as fh:
                caps = json.load(fh)
            off = float(cap.get("offset", 0))
            for c in caps:
                a0, b0 = c["from"] + off, min(c["to"] + off, total)
                if a0 >= total or b0 - a0 < 0.2:
                    continue
                cards.append({"lines": c["lines"], "from": round(a0, 3), "to": round(b0, 3), "anim": cap.get("anim", "highlight"),
                              "char_times": [max(0.0, x - c["from"]) for x in c["char_times"]],
                              **{k: cap[k] for k in ("font_size", "y", "accent", "color", "font", "cjk_font") if k in cap}})
        from make_card import layout as _layout
        for k, c in enumerate(cards):
            a, b = float(c["from"]), float(c["to"]); f = min(0.3, (b - a) / 3)
            n_chars = sum(len(re.sub(r"\[\[|\]\]|\s", "", ln)) for ln in c["lines"])
            if not c.get("char_times") and n_chars / max(0.1, b - a) > 9:
                warn.append(f"card {k + 1} \"{' / '.join(c['lines'])}\": {n_chars} characters in {b - a:.1f}s is hard to read; show it longer or shorten it")
            if b > total + 0.01:
                sys.exit(f"card {k}: ends at {b}s but the video is {total:.2f}s")
            font = c.get("font", pj.get("font")); cjk = c.get("cjk_font", pj.get("cjk_font"))
            kw = dict(font=P(font) if font else None, cjk_font=P(cjk) if cjk else None,
                      font_index=c.get("font_index", pj.get("font_index", 0)), font_size=c.get("font_size", round(72 * W / 1080)),
                      y=c.get("y"), accent=c.get("accent", pj.get("accent", "#B0F03E")), color=c.get("color", "#FFFFFF"), margin=pj.get("margin"))
            sizes = [it["sz"] for it in _layout(c["lines"], (W, H), kw["font"], kw["cjk_font"], kw["font_index"], kw["font_size"], kw["y"], margin=kw["margin"])]
            if sizes and min(sizes) < 40 * W / 1080:
                warn.append(f"card {k + 1}: text shrank to {min(sizes)}px to fit the safe width; split the line or use fewer words")
            anim = c.get("anim", "fade")
            if anim in anim_text.ANIMS:                              # animated text: a PNG sequence, shifted to its start time
                frames = os.path.join(tmp, f"card{k}")
                anim_text.render(frames, c["lines"], b - a, fps, anim, (W, H), c.get("reveal"), char_times=c.get("char_times"), **kw)
                ins += ["-framerate", fps, "-i", os.path.join(frames, "%05d.png")]
                fc.append(f"[{n}:v]format=rgba,setpts=PTS+{a}/TB[c{k}]")
                fc.append(f"[{prev}][c{k}]overlay=0:0:eof_action=pass:enable='between(t,{a},{b})':format=auto[o{k}]")
            else:
                png = os.path.join(tmp, f"card{k}.png")
                draw_card(png, c["lines"], (W, H), **kw)
                ins += ["-loop", "1", "-t", total, "-i", png]      # -loop 1, or the card vanishes after one frame
                fc.append(f"[{n}:v]format=rgba,fade=t=in:st={a}:d={f}:alpha=1,fade=t=out:st={b - f}:d={f}:alpha=1[c{k}]")
                y = {"fade": "0", "slide_up": f"if(lt(t,{a + f}),60*(1-(t-{a})/{f}),0)", "slide_down": f"if(lt(t,{a + f}),-60*(1-(t-{a})/{f}),0)"}.get(anim)
                if y is None:
                    sys.exit(f"card {k}: unknown anim '{anim}'. Use fade, slide_up, slide_down, {', '.join(anim_text.ANIMS)}")
                fc.append(f"[{prev}][c{k}]overlay=x=0:y='{y}':enable='between(t,{a},{b})':format=auto[o{k}]")
            prev = f"o{k}"; n += 1
        logo = pj.get("logo")
        if logo:
            lw = int(round(W * float(logo.get("width", 0.22)) / 2) * 2); m = int(logo.get("margin", round(W * 0.06)))
            px = {"left": str(m), "right": f"W-w-{m}", "center": "(W-w)/2"}; py = {"top": str(m), "bottom": f"H-h-{m}", "center": "(H-h)/2"}
            pos = logo.get("pos", "top-center").split("-"); v = pos[0]; h = pos[1] if len(pos) > 1 else "center"
            if v not in py or h not in px:
                sys.exit("logo.pos must look like top-left, top-center, center-center, bottom-right ...")
            la, lb = float(logo.get("from", 0)), float(logo.get("to", total))
            ins += ["-loop", "1", "-t", total, "-i", P(logo["file"])]
            fc.append(f"[{n}:v]scale={lw}:-1,format=rgba,fade=t=in:st={la}:d=0.3:alpha=1[lg]")
            fc.append(f"[{prev}][lg]overlay=x={px[h]}:y={py[v]}:enable='between(t,{la},{lb})':format=auto[ol]")
            prev = "ol"; n += 1
        fade = float(pj.get("fade", 0.3))
        fc.append(f"[{prev}]" + (f"fade=t=in:st=0:d={fade},fade=t=out:st={total - fade:.3f}:d={fade}," if fade else "") + "format=yuv420p[v]")
        # 4. music
        m = pj.get("music")
        if m:
            mi = info(P(m["file"])); ms = float(m.get("start", 0))
            if ms + total > mi["duration"] + 0.05:
                sys.exit(f"music is {mi['duration']:.1f}s; cannot take {total:.1f}s from {ms}s")
            ins += ["-ss", ms, "-t", total, "-i", P(m["file"])]
            fo = min(2.5, total / 4)
            fc.append(f"[{n}:a]aresample=48000,volume={m.get('volume', 1.0)},afade=t=in:st=0:d=0.5,afade=t=out:st={total - fo:.3f}:d={fo}[a]")
        else:
            ins += ["-f", "lavfi", "-t", total, "-i", "anullsrc=r=48000:cl=stereo"]
            fc.append(f"[{n}:a]anull[a]")
        cues = pj.get("cues", [])
        stage = os.path.join(tmp, "base.mp4") if cues else out
        run(ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", fps,
                   "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", stage])
        # 5. sound effects (picture is copied)
        if cues:
            mix(stage, out, cues, P(pj.get("sfx_dir", ".")), pj.get("duck", 0.5), pj.get("sfx_gain", 1.4))
        for w_ in warn:
            print("  WARN", w_)
        print(f"wrote {out}  ({total:.2f}s, {W}x{H})")
        return out
    finally:
        if keep_temp:
            print("temp files kept in", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("project", nargs="?"); p.add_argument("--keep-temp", action="store_true")
    p.add_argument("--list", action="store_true", help="list sizes, effects and transitions")
    a = p.parse_args()
    if a.list or not a.project:
        print("sizes:      ", ", ".join(f"{k} ({w}x{h})" for k, (w, h) in SIZES.items()), "or [width, height]")
        print("effects:    ", ", ".join(sorted(FX)), "  (+ per-shot: zoom, speed, cx, cy)")
        print("transitions:", ", ".join(TRANSITIONS))
        print("card anim:   fade, slide_up, slide_down,", ", ".join(anim_text.ANIMS))
        sys.exit(0)
    build(a.project, a.keep_temp)
