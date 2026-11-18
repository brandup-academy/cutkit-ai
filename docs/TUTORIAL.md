# 分步教程

目标：做一条 8 秒竖屏短片，然后改成你自己的内容。每一步都写了你应该看到的结果。

## 第 1 步：确认环境
```bash
python3 scripts/selftest.py
```
最后应该看到 5 行 `PASS`。看到 `ffmpeg not found`，说明还没装 ffmpeg，按 README 的"安装"处理。

## 第 2 步：看成片和项目文件
- 成片：`examples/out/demo_9x16.mp4`
- 项目文件：`examples/demo_project.json`

对照着看：`shots` 是三个镜头，`cards` 是两张字幕，`music` 是背景音乐，`cues` 是两个音效。

## 第 3 步：改一个镜头
把第二个镜头的 `"dur": 2.5` 改成 `"dur": 1.5`，然后重新生成：
```bash
python3 scripts/build.py examples/demo_project.json
```
成片变成 7 秒。这时会报错 `card 1: ends at 7.8s but the video is 7.00s`，因为第二张字幕超出了片长。
把它的 `from` / `to` 改成 `4.8` / `6.8` 再生成一次。工具会拦住这类错位，这是有意的。

## 第 4 步：加特效和转场
给第一个镜头加上 `"fx": ["grade", "flash"]`，给第二个镜头加上 `"transition": "slideleft"`。
```bash
python3 scripts/build.py --list
```
这条命令列出所有可用的名字。转场会让两个镜头重叠，所以片长会再缩短 0.4 秒。

## 第 5 步：换成横屏
把 `"size"` 改成 `"16:9"`。字幕的安全边距和字号会按宽度自动换算。

## 第 6 步：用 AI 做音效
1. 截出要配音的那一段，6 秒、无声：
   ```bash
   python3 scripts/cut_clip.py 你的素材.mp4 17.2 clip.mp4
   ```
2. 把 `clip.mp4` 上传到一个"视频生成音效"的 AI 工具，写清楚想要的声音，下载结果。
3. 把音效文件放进 `sfx_dir`，在 `cues` 里加一条，`at` 写它在成片里出现的秒数。

一条音效通常是整段混在一起的声音。只想要其中一下，用 `start` / `end` 截出来。

## 第 7 步：检查
```bash
python3 scripts/check.py examples/out/demo_9x16.mp4 --expect 1080x1920 --at 3.0 --sheet sheet.jpg
```
你会看到尺寸、每秒音量、`--at` 那一秒音效是否真的比前面响，以及一张 12 格缩略图。
这是测量，不能代替试听，发布前自己播放一遍。

## 第 8 步：让 AI 助手来做
把这个文件夹交给 Claude Code 或 Codex，用一句话提需求，比如：
"用 footage/ 里的素材做一条 30 秒竖屏，开头三秒要有冲击力，结尾写 COMMENT PLAY。"
助手会读 `AGENTS.md` 或 `SKILL.md` 和 `rules/`，写出项目文件，运行 `build.py` 和 `check.py`。
你的个人要求写进 `rules/my-preferences.md`，它每次都会遵守。

## 第 9 步：一句话做一条广告
```bash
python3 examples/ad_example/make_placeholder_assets.py
python3 scripts/ad.py check examples/ad_example
python3 scripts/ad.py build examples/ad_example
```
`check` 会列出每个镜头的状态、方案里的问题，以及还要生成什么、大约多少 Sparks。
`build` 出的是预览片（文件名带 `_animatic`），因为后三个镜头还是分镜图。这一步是为了让你在花钱生成视频之前先确认节奏和文案。
换成真的素材：按 `plan.json` 里每个镜头的 `file` 文件名保存生成的视频，再运行一次 `build`，就是成片。

自己开一条新的：
```bash
python3 scripts/ad.py new "你的一句话" --recipe restaurant_promo_15s --dir ads/my_ad
```
然后让 AI 助手填写 `ads/my_ad/plan.json`，或者自己照 `examples/ad_example/plan.json` 的样子填。

## 第 10 步：给口播视频加自动字幕
```bash
pip install faster-whisper
python3 scripts/captions.py 口播.mp4 --out captions.json --srt 口播.srt --lang zh --hint "BrandUp, WhatsApp"
```
它会列出每条字幕和时间。检查一遍，有错字就加 `--fix "错=对"` 重新运行。
然后在项目文件里，镜头用口播视频本身，音乐的位置放口播的声音，再加上：
```json
"captions": {"file": "captions.json", "anim": "highlight", "font_size": 90}
```
`highlight` 是说到哪个词哪个词变色；`words` 是说到才出现；`typewriter` 是逐字打出来。

## 常见问题
- **字幕是方块或乱码**：系统里没有合适的字体。在项目文件里用 `font` / `cjk_font` 指定字体文件。
- **`cannot take ...s from ...s`**：素材不够长。减小 `dur`、`start` 或 `speed`。
- **字幕把名字听错了**：用 `--hint` 写上品牌名和人名；还错就用 `--fix`。
- **识别很慢**：换小一点的模型 `--model base`，准确率会下降一些。
- **音效听不清**：调大该条的 `gain`，或把 `duck` 调小（比如 0.35）。
