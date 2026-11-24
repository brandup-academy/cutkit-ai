---
name: cutkit-ai
description: Make and edit short video ads and promo videos with ffmpeg - one-sentence ad workflow (recipe, storyboard, cost quote, Bloomway assets), 9:16 or 16:9 cuts, effects, transitions, animated text, auto subtitles, brand intro/outro, music and per-shot sound effects. Use when asked to make an ad from a sentence, or to cut, re-cut, caption, add text, effects or sound to a promo, trailer, hook or social video.
---

# Promo video editing

## Where things are
The scripts, recipes, rules and docs sit next to this SKILL.md (the skill's base directory). Run them by absolute path, e.g.
`python3 "<skill base directory>/scripts/build.py" project.json`. Write projects, ads and outputs in the user's working folder, never inside the skill folder.
ffmpeg: `ffmpeg` on PATH, the `FFMPEG` environment variable, or `pip install imageio-ffmpeg` (found automatically). Motion titles also need ffprobe (`FFPROBE=...` if it is not on PATH).
Machine-specific notes, if any, are in `rules/my-preferences.md` (not published).

## What this repository is
A toolkit that builds a short promo video from one JSON project file using ffmpeg and Python. There is no GUI.

## Workflow
1. Read `rules/general.md`, then `rules/my-preferences.md` if it exists. The preferences file wins where they differ.
2. Inspect the footage before choosing shots: use `python3 scripts/check.py FILE --sheet sheet.jpg` and look at the contact sheet. Do not guess what a clip contains.
3. Write a project file (see `docs/PROJECT_FORMAT.md`; `examples/demo_project.json` and `examples/fx_project.json` are working examples). Run `python3 scripts/build.py --list` for the valid effect, transition and text-animation names.
4. Build: `python3 scripts/build.py project.json`. It stops with a plain message if a shot, card or cue does not fit; fix the project file, do not work around the check.
5. Sound effects: `python3 scripts/cut_clip.py SRC START clip.mp4` makes a 6 s silent clip for a video-to-sound-effect tool. Generating audio usually costs credits: tell the user the cost and get a yes first. Add the result as a cue; trim with `start`/`end` so the loud part lands on the action.
6. Verify: `python3 scripts/check.py out.mp4 --expect WxH --at T ...` for each cue time, plus `--sheet`. Look at the sheet.
7. Report what you measured and say plainly that you did not listen to or watch the result. Name anything that is approximate.

## One-sentence ad workflow (`scripts/ad.py`)
Use this when the user asks for an ad from a short description.
1. Run `python3 scripts/ad.py recipes`, pick the closest recipe, and create the plan: `ad.py new "<their sentence>" --recipe NAME --dir ads/<slug> [--brand brand.json]`.
2. Ask the user the recipe's questions (at most three) and for a product photo if they have one. Do not invent offers, prices, dates, phone numbers or claims; leave a beat's text empty rather than guess.
3. Fill `plan.json`: title, answers, and for every beat an `image_prompt`, a `video_prompt`, on-screen `text` (short: the checker flags long lines), optional `vo` and `sfx_prompt`. Follow each beat's `guide`. Keep the product and people consistent across prompts.
4. Run `ad.py check`. Fix every problem it lists. Show the user the shot table and the cost estimate. Prices in `prices.example.json` are examples: read the real price from Bloomway and say so if you could not.
5. Stage 1, storyboard: after the user agrees to the storyboard cost, generate one still per beat (Bloomway image generation, via MCP or the web workspace) and save each to the beat's `storyboard` path. Run `ad.py build` to make the animatic and show it.
6. Stage 2, production: only after the user approves the animatic AND the remaining cost, generate each beat's video (image-to-video from its still), the music, any voiceover lines and sound effects, saving to the paths in the plan. Generate one item first to confirm the price and quality before the rest.
7. Run `ad.py build`, then `scripts/check.py` on the result with `--expect` and `--sheet`. Report what you measured and that you did not watch or listen to it.
Never start a paid generation without an explicit yes for that stage. `ad.py` itself never spends credits.

## Speech captions (`scripts/captions.py`, optional)
For footage with real speech (talking heads, interviews). Needs `pip install faster-whisper`; the model downloads on first use (~0.5 GB for `small`); tell the user before downloading.
`python3 scripts/captions.py MEDIA --out captions.json --srt out.srt --lang zh|en|ms --hint "brand names"`, then add `"captions": {"file": "captions.json", "anim": "highlight"}` to the project.
Read the printed captions and fix misheard names with `--fix "wrong=right"`. Recognition gives words and timings only: it cannot judge music or sound effects.
For ads whose voiceover is generated from a script, captions are not needed: the text is already in the plan.

## Brand intro / outro (`scripts/motion.py`, optional)
A shot can be `{"motion": {"title": "...", "kicker": "...", "subtitle": "..."}, "dur": 3}`; it is rendered with HyperFrames (Apache-2.0).
Needs Node.js 22+, ffprobe (full FFmpeg) and internet. Before the first render, tell the user it downloads HyperFrames and a headless Chrome, and that HyperFrames sends usage telemetry unless they run `npx hyperframes telemetry disable`.
Only put words the user supplied in a motion title. Do not put URLs in it.

## Warnings
Read the `WARN` lines `build.py` prints (too-short shots, text too dense to read, text shrunk to fit) and fix them before showing the result.

## Conventions
- Card and cue times refer to the finished timeline. Each transition shortens the timeline by its duration.
- Never overwrite the user's source footage. Write outputs to an `out/` folder.
- Only use text, numbers and claims the user supplied. Do not add copy of your own.
- To add sound to a screen recording of an earlier render, run `scripts/find_offset.py` first and prefer the original render.

## Setup
Python 3.9+, `pip install pillow numpy imageio-ffmpeg` (or ffmpeg on PATH / `FFMPEG` env var). `python3 scripts/selftest.py` must print five PASS lines.
