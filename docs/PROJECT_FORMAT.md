# Project file format

A project is one JSON file. Paths are relative to that file. Lines starting with `//` are ignored.

## Top level
| key | default | meaning |
|---|---|---|
| `out` | `out.mp4` | output file |
| `size` | `"9:16"` | `"9:16"` 1080x1920, `"16:9"` 1920x1080, `"4:5"` 1080x1350, `"1:1"` 1080x1080, or `[width, height]` |
| `fps` | 30 | frame rate |
| `fade` | 0.3 | fade the picture in and out, seconds; 0 turns it off |
| `look` | `[]` | effects applied to every shot |
| `shots` | required | list of shots, in order |
| `cards` | `[]` | text cards |
| `font`, `cjk_font` | system font | font files for Latin text and for Chinese/Japanese/Korean text |
| `font_index` | 0 | face inside a `.ttc` collection |
| `accent` | `#B0F03E` | colour of `[[highlighted]]` words |
| `margin` | 90 px per 1080 width | safe margin on each side for text |
| `logo` | none | `{"file", "width": 0.22, "pos": "top-center", "from", "to"}`; width is a fraction of the frame, pos is `top|center|bottom`-`left|center|right` |
| `captions` | none | `{"file": "captions.json", "anim": "highlight", "offset": 0, "font_size", "y", "accent"}`; captions from `scripts/captions.py`, timed per word. `offset` shifts them if the audio starts later in the video |
| `music` | none | `{"file", "start", "volume"}` |
| `sfx_dir` | project folder | folder of sound-effect files |
| `duck` | 0.5 | music level while an effect plays |
| `sfx_gain` | 1.4 | base gain for effects |
| `cues` | `[]` | sound-effect cues |

## Shot
| key | default | meaning |
|---|---|---|
| `src`, `image` or `motion` | required | a video file, a still image, or an animated brand title: `{"title", "kicker", "subtitle", "accent", "bg", "ink", "font"}` rendered with HyperFrames (optional; Node.js 22+, ffprobe, internet) |
| `start` | 0 | where to start in the source, seconds |
| `dur` | required | length in the finished video, seconds |
| `cx`, `cy` | 0.5 | crop centre, 0 = left/top, 1 = right/bottom |
| `zoom` | 0.07 | slow push-in amount; 0 = none, 0.25 = strong |
| `speed` | 1.0 | 2.0 = double speed, 0.5 = slow motion (uses `dur * speed` seconds of source) |
| `fx` | `[]` | effects, applied in order |
| `transition` | cut | how this shot arrives: a name, or `{"type": name, "dur": 0.4}` |

Effects: `grade` `warm` `cool` `bw` `vignette` `grain` `sharpen` `glitch` `mirror` `flash` `dip` `shake` `reverse`.

Transitions: `fade` `fadeblack` `fadewhite` `wipeleft` `wiperight` `wipeup` `wipedown` `slideleft` `slideright` `slideup`
`slidedown` `circleopen` `circleclose` `dissolve` `pixelize` `radial` `zoomin` `smoothleft` `smoothright`.

A transition overlaps two shots, so the video gets shorter by the transition's length. Card and cue times refer to the finished timeline.

## Card
| key | default | meaning |
|---|---|---|
| `lines` | required | list of text lines; `[[words]]` use the accent colour |
| `from`, `to` | required | when it shows, seconds |
| `font_size` | 72 at 1080 wide | starting size; if any line is too wide for the safe width, every line of that card shrinks to the same size |
| `y` | 61% of height | top of the first line, pixels |
| `anim` | `fade` | `fade`, `slide_up`, `slide_down`, or animated text: `typewriter`, `words`, `highlight`, `pop` |
| `reveal` | automatic | seconds the animated reveal takes; it always ends before the card does |
| `font`, `cjk_font`, `font_index`, `accent`, `color` | project values | per-card overrides |

## Cue
| key | default | meaning |
|---|---|---|
| `file` | required | audio file inside `sfx_dir` |
| `at` | required | when it starts in the video, seconds |
| `start`, `end` | whole file | part of the audio file to use |
| `gain` | 1.0 | multiplier on top of `sfx_gain` |

## Ad plan (`plan.json`, used by `scripts/ad.py`)
Created by `ad.py new` from a recipe. Each beat has: `role`, `dur`, `guide` (what the recipe wants), `image_prompt`, `video_prompt`,
`text` (on-screen lines), `anim`, `vo` (voiceover line, optional), `sfx_prompt` (optional), `fx`, `transition`, and the file names the
assets must be saved to: `storyboard` (still), `file` (video), `vo_file`, `sfx_file`. `music.prompt` / `music.file` describe the music.
`brand` points to a brand kit like `brand.example.json`. A beat with `"logo": true` shows the brand logo.

## Warnings
`build.py` prints `WARN` lines (the video is still made) when a shot is shorter than 0.8 s, when a card has more than about
9 characters per second to read, or when a line had to shrink below 40 px (at 1080 wide) to fit the safe margins.
