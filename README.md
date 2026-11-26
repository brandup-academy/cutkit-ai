# CutKit

[![selftest](https://github.com/brandup-academy/cutkit-ai/actions/workflows/test.yml/badge.svg)](https://github.com/brandup-academy/cutkit-ai/actions/workflows/test.yml)

English · [中文](README.zh-CN.md)

**Make a short video ad from one sentence, with Claude Code or Codex doing the editing.**
The AI assistant writes the plan, you generate the shots, and CutKit cuts them into a finished ad with captions, transitions, music and sound effects. It is plain ffmpeg and Python, so it also works from the command line on its own.

<img src="docs/media/cutkit-showreel.gif" height="292" alt="A 16:9 AI showreel cut by CutKit, with captions such as NO CAMERA. NO CREW."> <img src="docs/media/cutkit-demo.gif" height="292" alt="A 14-second vertical coffee ad built by CutKit: five shots with typewriter captions">

*Left: a 16:9 showreel. Right: a 14-second 9:16 product ad. Each was cut by CutKit from one project file: shots, captions, music and sound effects. The footage is AI-generated, and Kopi Pagi is a made-up brand.*

## Quick start

```bash
# Mac / Linux: install as a Claude Code skill
git clone https://github.com/brandup-academy/cutkit-ai.git ~/.claude/skills/cutkit-ai
cd ~/.claude/skills/cutkit-ai
pip install pillow numpy imageio-ffmpeg
python3 scripts/selftest.py
```

The last command makes a set of copyright-free practice footage, builds an 8-second vertical video and checks the result. Every line it prints should start with `PASS`; the video is at `examples/out/demo_9x16.mp4`.

Then open Claude Code and describe the ad you want, for example: *"Make a 15-second ad for my cold brew coffee."*

```powershell
# Windows (PowerShell)
git clone https://github.com/brandup-academy/cutkit-ai.git "$env:USERPROFILE\.claude\skills\cutkit-ai"
```

Needs Python 3.9+. FFmpeg comes with `imageio-ffmpeg`; if you already have ffmpeg you can skip that package, or point to it with the `FFMPEG` environment variable. To update later, run `git pull` in the folder.

## What it does

| Feature | Details |
|---|---|
| Sizes | `9:16` vertical, `16:9` horizontal, `4:5` feed, `1:1`, or any `[width, height]` |
| Shots | Trim, crop position, push-in zoom, speed change, reverse, still images |
| Effects | Colour grades (grade / warm / cool / bw), vignette, grain, sharpen, flash, shake, glitch, mirror |
| Transitions | 19, including fades, flash to white, slides, wipes, circle open, pixelize and zoom |
| Caption cards | Any ttf/otf/ttc font, separate fonts for Latin and Chinese text, accent colour, safe margins, fade or slide in |
| Animated text | Typewriter, word by word, word highlight, pop; the text always finishes before the shot ends |
| Auto subtitles | Recognises speech in English, Chinese, Malay and more; each word lights up as it is spoken; exports `.srt` (optional) |
| Logo | Any corner or centred; can appear only at the end |
| Brand intro and outro | Animated title with letter-by-letter reveal, rendered with HyperFrames (optional) |
| Quality warnings | Warns when text is too small, too dense to read in time, or a shot is too short |
| One-sentence ad | 4 ad recipes, a brand profile file, a storyboard preview first, and a cost quote before anything is generated |
| Music | Start point, volume, automatic fade in and out |
| Sound effects | Placed by time; the music dips automatically under each one |
| Checks | Verify without watching: size, loudness per second, frozen frames, contact sheet |

Run `python3 scripts/build.py --list` for every effect, transition and text animation name.

## One-sentence ad

```bash
python3 scripts/ad.py recipes                          # list the ad recipes
python3 scripts/ad.py new "Make a 15-second ad for my cold brew coffee" --recipe product_showcase_15s --dir ads/kopi
python3 scripts/ad.py check ads/kopi                   # check the plan, list what still needs generating and the rough cost
python3 scripts/ad.py build ads/kopi                   # build; shots without video yet use their storyboard stills
```

The flow: one sentence plus two or three questions → the AI assistant writes the storyboard and copy from a recipe (`plan.json`) → cheap storyboard stills first, cut into a preview for you to approve → after you approve it and the cost, the videos, music, voiceover and sound effects are generated → CutKit edits and checks the result.

`examples/ad_example/` is a finished example plan. `scripts/ad.py` never spends credits itself: generation is done by you or your AI assistant in Bloomway.

Recipes are in `recipes/` (product showcase, restaurant promo, hiring, course or event) and can be edited. Fill in `brand.example.json` once and every ad uses it. `prices.example.json` holds example prices; replace them with the prices Bloomway shows you.

## What it is not

It is not CapCut: there is no interface, no timeline preview, no sticker templates, no keyframe animation, no beauty filter or background removal. You or your AI assistant decide which shot goes where; CutKit carries that decision out exactly, and can repeat it.

## Optional features

**Auto subtitles**

```bash
pip install faster-whisper
python3 scripts/captions.py talk.mp4 --out captions.json --srt talk.srt --hint "Brand name, WhatsApp"
```

Then add `"captions": {"file": "captions.json", "anim": "highlight"}` to the project file. The first run downloads the speech model (`small` by default, about 0.5 GB). Brand and people's names are often misheard: pass them with `--hint` and fix the rest with `--fix "wrong=right"`. Read the subtitles before you publish.

**Brand intro and outro**

```bash
npx hyperframes telemetry disable      # optional: do not send usage statistics to HeyGen
python3 scripts/motion.py intro.mp4 --title "BrandUp Academy" --kicker "AI VIDEO LAB" --subtitle "Learn AI. Create better content."
```

Or put it in a shot in the project file: `{"motion": {"title": "...", "kicker": "...", "subtitle": "..."}, "dur": 3}` (see `examples/motion_project.json`). Needs Node.js 22+, ffprobe (a full FFmpeg) and internet. Details: [docs/RESOURCES.md](docs/RESOURCES.md).

## More examples

```bash
python3 scripts/build.py examples/fx_project.json
```

Builds a horizontal demo of the effects and transitions at `examples/out/fx_16x9.mp4`.

## Files

| File | What it is for |
|---|---|
| `scripts/ad.py` | One-sentence ad: create the plan, check and quote, build |
| `scripts/build.py` | Build a video from one project file |
| `scripts/anim_text.py` | Animated text |
| `scripts/captions.py` | Auto subtitles (optional) |
| `scripts/motion.py` + `motion/` | Brand intro and outro (optional, HyperFrames) |
| `scripts/check.py` | Check a finished video |
| `scripts/make_card.py` | Draw a single caption card |
| `scripts/mix_sfx.py` | Add sound effects to an existing video |
| `scripts/cut_clip.py` | Cut a silent clip to give an AI sound-effect tool |
| `scripts/find_offset.py` | Find the offset between a screen recording and the original render |
| `docs/TUTORIAL.md` | Step-by-step tutorial |
| `docs/PROJECT_FORMAT.md` | Every option in the project file |
| `docs/RESOURCES.md` | Other tools you can install: voiceover, web design, motion graphics |
| `recipes/` | Ad recipes |
| `brand.example.json` / `prices.example.json` | Example brand profile and price list |
| `rules/general.md` | General editing rules |
| `rules/my-preferences.example.md` | Example of a personal preferences file |
| `AGENTS.md` / `SKILL.md` | Instructions for Codex and Claude Code |

## What is tested

Tested on macOS with ffmpeg 7.1 and Python 3.9. On every push, GitHub Actions also runs the self-test (`scripts/selftest.py`) on Windows and Ubuntu with Python 3.11: it builds the 8-second demo, the animated-text example and the one-sentence ad example, then checks size, length and sound.
Auto subtitles and the brand intro/outro are not part of that automated run, and it is the only testing done on Windows and Linux so far.

- The animated text and all scripts are this repository's own code and depend only on Pillow, numpy and ffmpeg. No third-party programs are bundled.
- Brand intro and outro call [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0), downloaded at run time through `npx`. It is not included in this repository.
- Auto subtitles call [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT), installed separately. It and its speech models are not included.
- Apart from the two preview images above, no footage, music or fonts are bundled. Without a font setting, CutKit looks for a system font; use fonts you have the right to use.
- `check.py` measures; it does not listen. Play the video yourself before you publish.

## Using it with Bloomway

This toolkit does the editing. Footage, music and sound effects can come from [Bloomway](https://bloomway.ai/?ref=BWUF5CQXX); shots can be planned first in Bloomway's open-source [World Director](https://github.com/bloomway-ai/bloomway-world-director) (MIT, [try it in the browser](https://bloomway-ai.github.io/bloomway-world-director/)).

1. **Previs** in World Director: blockout world, character blocking, camera paths.
2. **Generate** shots and music in Bloomway, in the web workspace or from an AI assistant over MCP.
3. **Sound effects:** cut a 6 s silent clip with `scripts/cut_clip.py` and run Bloomway's video-to-sound-effect on it.
4. **Assemble** with `scripts/build.py` and verify with `scripts/check.py`.

World Director produces blockout previs, not final footage. Follow Bloomway's terms of use for generated content.
The Bloomway links on this page are BrandUp's referral link: we get a reward if you sign up through it; your price is the same.
Example: [BLOOMWAY RUN](https://bloomway-run.vercel.app), a playable AI film game whose visuals and music were generated with Bloomway; its trailers were cut and sound-designed with this workflow.

## Third-party licenses and publishing

CutKit code is licensed under [MIT](LICENSE). For redistribution, check each component's license for the version you ship. HyperFrames requires the Apache-2.0 license, applicable notices and a notice in modified files. FFmpeg's terms depend on its build. [HyperFrames license](https://github.com/heygen-com/hyperframes/blob/main/LICENSE) · [FFmpeg legal](https://ffmpeg.org/legal.html)

[Hypit](https://github.com/hypit-ai/hypit/blob/main/LICENSE) is a separate tool a team can evaluate. Its license permits internal and client video production and requires prior written commercial authorization for commercial redistribution or third-party hosting of its functionality. Rights in source material and third-party model terms still apply.

The current workflow ends with a video export for the account owner to review, listen to and publish manually. Instagram monitoring and API publishing are planned features.

## Built with Claude

CutKit was built with Claude Code, using Claude Opus 5.5 and Claude Fable 5.2.

## About

**[BrandUp Academy](https://www.brandupdesignmarketing.com/academy/)** is the training brand of BrandUp Design Marketing, an ad agency that plans, produces and runs Facebook and Instagram advertising for brands. Its courses are taught by the agency's teaching team.
The Academy is online only. Its course is the **AI Video & Short Drama Masterclass**, a recorded online course; the syllabus is on the [course page](https://www.brandupdesignmarketing.com/academy/#masterclass). This toolkit is the open-source auto-editing step of the workflow on the [AI Ad Toolkit](https://www.brandupdesignmarketing.com/academy/ai-tools/) page.

*Learn AI. Create better content. Grow your brand.*

MIT License © 2026 BrandUp One Sdn Bhd
