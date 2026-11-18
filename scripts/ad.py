#!/usr/bin/env python3
"""One-sentence ad workflow: sentence -> plan -> storyboard + quote -> assets -> finished ad.

  python3 scripts/ad.py recipes                               list ad recipes
  python3 scripts/ad.py new "sentence" --recipe NAME --dir ads/my_ad [--brand brand.json]
  python3 scripts/ad.py check ads/my_ad                       validate the plan, list missing assets, quote the cost
  python3 scripts/ad.py build ads/my_ad                       build the ad (uses storyboard stills for shots not generated yet)

The plan (plan.json) is written by a person or an AI assistant. Assets are generated separately
(e.g. with Bloomway) and saved to the file names the plan lists. This script never spends credits.
"""
import argparse, json, os, re, sys
from common import info
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def jload(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)

def jsave(p, d):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)

def recipes():
    d = os.path.join(ROOT, "recipes")
    return {f[:-5]: jload(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".json")}

def cmd_recipes(_):
    for k, r in recipes().items():
        total = sum(b["dur"] for b in r["beats"])
        print(f"{k:24s} {r['name']}  ({total:g}s, {len(r['beats'])} shots)  {r['use_when']}")

def cmd_new(a):
    rs = recipes()
    if a.recipe not in rs:
        sys.exit(f"unknown recipe '{a.recipe}'. Run: python3 scripts/ad.py recipes")
    r = rs[a.recipe]
    if os.path.exists(os.path.join(a.dir, "plan.json")):
        sys.exit(f"{a.dir}/plan.json already exists; choose another --dir")
    os.makedirs(os.path.join(a.dir, "assets"), exist_ok=True)
    beats = []
    for i, b in enumerate(r["beats"], 1):
        bid = f"b{i}"
        beats.append({"id": bid, "role": b["role"], "dur": b["dur"],
                      "guide": {"visual": b["visual"], "text": b["text"]},
                      "image_prompt": "", "video_prompt": "", "text": [], "anim": b.get("anim", "fade"),
                      "vo": "", "sfx_prompt": "",
                      "fx": b.get("fx", []), **({"transition": b["transition"]} if b.get("transition") else {}),
                      **({"logo": True} if b.get("logo") else {}),
                      "storyboard": f"assets/{bid}.jpg", "file": f"assets/{bid}.mp4",
                      "vo_file": f"assets/{bid}_vo.mp3", "sfx_file": f"assets/{bid}_sfx.mp3"})
    plan = {"title": "", "sentence": a.sentence, "recipe": a.recipe, "size": r["size"],
            "brand": os.path.relpath(a.brand, a.dir) if a.brand else None,
            "answers": {q: "" for q in r["questions"]},
            "music": {"prompt": r["music"], "file": "assets/music.mp3"}, "beats": beats}
    jsave(os.path.join(a.dir, "plan.json"), plan)
    print(f"created {a.dir}/plan.json from recipe '{a.recipe}'\nAsk the owner these before writing the plan:")
    for q in r["questions"]:
        print("  -", q)

def _brand(plan, d):
    b = plan.get("brand")
    return jload(os.path.join(d, b)) if b else {}

def _timeline(beats):
    """Start time of each beat in the finished video (a transition overlaps the previous shot)."""
    t, starts = 0.0, []
    for i, b in enumerate(beats):
        tr = b.get("transition")
        if i and tr:
            t -= float(tr.get("dur", 0.4)) if isinstance(tr, dict) else 0.4
        starts.append(t); t += float(b["dur"])
    return starts, t

def _exists(d, rel):
    return bool(rel) and os.path.exists(os.path.join(d, rel))

def analyse(d):
    plan = jload(os.path.join(d, "plan.json"))
    problems, need = [], {"storyboard_image": 0, "video_clip": 0, "music": 0, "voiceover_line": 0, "sound_effect": 0}
    if not plan.get("title"):
        problems.append("title is empty")
    for q, ans in (plan.get("answers") or {}).items():
        if not ans:
            problems.append(f"unanswered: {q}")
    rows = []
    for b in plan["beats"]:
        st = []
        for key, label in (("image_prompt", "image prompt"), ("video_prompt", "video prompt")):
            if not b.get(key):
                problems.append(f"{b['id']}: {label} is empty")
        if not b.get("text"):
            problems.append(f"{b['id']}: no on-screen text (use [] on purpose only)") if b["role"] in ("hook", "cta") else None
        for line in b.get("text", []):
            plain = re.sub(r"\[\[|\]\]", "", line)
            limit = 12 if re.search(r"[　-鿿]", plain) else 24
            if len(plain) > limit:
                problems.append(f"{b['id']}: line too long for a phone screen ({len(plain)} > {limit}): {plain}")
        has_v, has_s = _exists(d, b.get("file")), _exists(d, b.get("storyboard"))
        if not has_s and not has_v: need["storyboard_image"] += 1
        if not has_v: need["video_clip"] += 1
        if has_v and info(os.path.join(d, b["file"]))["duration"] + 0.05 < b["dur"]:
            problems.append(f"{b['id']}: video is shorter than the shot ({b['dur']}s)")
        if b.get("vo"):
            if _exists(d, b.get("vo_file")):
                vd = info(os.path.join(d, b["vo_file"]))["duration"]
                if vd > b["dur"] - 0.2:
                    problems.append(f"{b['id']}: voiceover is {vd:.1f}s but the shot is {b['dur']}s; shorten the line or lengthen the shot")
            else:
                need["voiceover_line"] += 1
        if b.get("sfx_prompt") and not _exists(d, b.get("sfx_file")):
            need["sound_effect"] += 1
        st.append("video" if has_v else ("still" if has_s else "MISSING"))
        rows.append((b["id"], b["role"], b["dur"], st[0], " / ".join(b.get("text", []))))
    m = plan.get("music") or {}
    if m.get("prompt") and not _exists(d, m.get("file")):
        need["music"] += 1
    return plan, rows, problems, need

def cmd_check(a):
    plan, rows, problems, need = analyse(a.dir)
    _, total = _timeline(plan["beats"])
    print(f"{plan.get('title') or '(untitled)'}  |  {plan['recipe']}  |  {plan['size']}  |  {total:.1f}s\n\"{plan['sentence']}\"\n")
    for r in rows:
        print(f"  {r[0]:4s} {r[1]:10s} {r[2]:>4g}s  {r[3]:8s} {r[4]}")
    print("\nProblems:" if problems else "\nNo problems found in the plan.")
    for p in problems:
        print("  -", p)
    pf = os.path.join(a.dir, "prices.json"); example = not os.path.exists(pf)
    prices = jload(os.path.join(ROOT, "prices.example.json") if example else pf)
    print("\nStill to generate" + (" (EXAMPLE prices: confirm real prices before spending)" if example else "") + ":")
    cost = 0
    for k, n in need.items():
        if n:
            c = n * prices.get(k, 0); cost += c
            print(f"  {n} x {k.replace('_', ' ')} @ {prices.get(k, '?')} = {c}")
    print(f"  total: about {cost} Sparks" if cost else "  nothing: all assets are present")
    sb = need["storyboard_image"] * prices.get("storyboard_image", 0)
    if need["storyboard_image"]:
        print(f"  (storyboard only, to approve before video: about {sb} Sparks)")
    return 1 if problems else 0

def cmd_build(a):
    from build import build
    d = a.dir
    plan, rows, problems, need = analyse(d)
    brand = _brand(plan, d); beats = plan["beats"]
    starts, total = _timeline(beats)
    shots, cards, cues, stills = [], [], [], 0
    for b, t0 in zip(beats, starts):
        dur = float(b["dur"])
        common = {k: b[k] for k in ("fx", "transition", "zoom", "cx", "cy", "speed") if k in b}
        if _exists(d, b.get("file")):
            shots.append({"src": b["file"], "start": b.get("start", 0), "dur": dur, **common})
        elif _exists(d, b.get("storyboard")):
            shots.append({"image": b["storyboard"], "dur": dur, **common}); stills += 1
        else:
            sys.exit(f"{b['id']}: neither {b.get('file')} nor {b.get('storyboard')} exists. Run `ad.py check` to see what to generate.")
        if b.get("text"):
            cards.append({"lines": b["text"], "from": round(t0 + 0.25, 2), "to": round(t0 + dur - 0.15, 2), "anim": b.get("anim", "fade"),
                          **({"font_size": b["font_size"]} if b.get("font_size") else {})})
        if b.get("vo") and _exists(d, b.get("vo_file")):
            cues.append({"file": b["vo_file"], "at": round(t0 + 0.15, 2), "gain": 0.85})
        if _exists(d, b.get("sfx_file")):
            sd = info(os.path.join(d, b["sfx_file"]))["duration"]
            cues.append({"file": b["sfx_file"], "at": round(t0 + float(b.get("sfx_at", 0)), 2), "end": round(min(sd, dur), 2), "gain": float(b.get("sfx_gain", 0.8))})
    slug = re.sub(r"[^a-z0-9]+", "_", (plan.get("title") or "ad").lower()).strip("_") or "ad"
    pj = {"out": f"out/{slug}{'_animatic' if stills else ''}.mp4", "size": plan["size"], "shots": shots, "cards": cards, "cues": cues, "sfx_dir": "."}
    for k in ("accent", "font", "cjk_font", "font_index"):
        if brand.get(k) is not None:
            pj[k] = brand[k]
    bdir = os.path.dirname(os.path.join(d, plan["brand"])) if plan.get("brand") else d
    for k in ("font", "cjk_font"):
        if pj.get(k):
            pj[k] = os.path.relpath(os.path.join(bdir, pj[k]), d)
    if brand.get("logo"):
        on = [t for b, t in zip(beats, starts) if b.get("logo")]
        pj["logo"] = {"file": os.path.relpath(os.path.join(bdir, brand["logo"]), d), "width": brand.get("logo_width", 0.3),
                      "pos": brand.get("logo_pos", "top-center"), "from": round(on[0] + 0.2, 2) if on else 0}
    m = plan.get("music") or {}
    if _exists(d, m.get("file")):
        pj["music"] = {"file": m["file"], "start": m.get("start", 0), "volume": m.get("volume", 1.0)}
    jsave(os.path.join(d, "project.json"), pj)
    out = build(os.path.join(d, "project.json"))
    if stills:
        print(f"NOTE: {stills} shot(s) use storyboard stills. This is an animatic for approval, not the final ad.")
    if not pj.get("music"):
        print("NOTE: no music file yet; the ad has no music bed.")
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("recipes")
    n = sub.add_parser("new"); n.add_argument("sentence"); n.add_argument("--recipe", required=True); n.add_argument("--dir", required=True); n.add_argument("--brand")
    c = sub.add_parser("check"); c.add_argument("dir")
    b = sub.add_parser("build"); b.add_argument("dir")
    a = p.parse_args()
    sys.exit({"recipes": cmd_recipes, "new": cmd_new, "check": cmd_check, "build": cmd_build}[a.cmd](a) or 0)
