# cutkit-ai

[![selftest](https://github.com/brandup-academy/cutkit-ai/actions/workflows/test.yml/badge.svg)](https://github.com/brandup-academy/cutkit-ai/actions/workflows/test.yml)

不会剪辑的人，也能用一句话做出一条广告短片：AI 助手写方案，Bloomway 生成画面和声音，这个工具包负责剪辑。
它也可以单独使用：一个项目文件，做出带字幕、转场、特效、音乐和音效的短视频。底层只有 ffmpeg 和 Python，
所以 Claude Code、Codex 或你自己敲命令都能用。仓库里不含任何画面、音乐或字体。

A small ffmpeg + Python toolkit that builds a short promo video from one project file. No media or fonts are bundled.

## 它能做什么
| 能力 | 说明 |
|---|---|
| 画幅 | `9:16` 竖屏、`16:9` 横屏、`4:5` 信息流、`1:1`，或任意 `[宽, 高]` |
| 镜头 | 截取、裁切位置、推近、变速、倒放、静态图 |
| 画面特效 | 调色（grade / warm / cool / bw）、暗角、颗粒、锐化、闪白、抖动、色差故障、镜像 |
| 转场 | 19 种：淡入淡出、闪白、滑动、擦除、圆形展开、像素化、缩放等 |
| 字幕卡 | 任意 ttf/otf/ttc 字体，中英文分别指定，强调色，自动留安全边距，淡入或滑入 |
| 动态文字 | 打字机、逐词弹出、逐词高亮、整体弹入，文字一定在镜头结束前出完 |
| 自动字幕 | 识别中文、英文、马来语等的语音，每个词说到时才亮起或出现，并可导出 .srt（可选功能） |
| Logo | 放在任意角落或居中，可只在结尾出现 |
| 品牌片头片尾 | 字母逐个弹出、光晕、强调线的动画标题，用 HyperFrames 渲染（可选功能） |
| 质量提醒 | 字太小、字太多来不及读、镜头太短时，出片时会提醒 |
| 一句话广告 | 4 个广告配方、品牌资料文件、先看分镜预览、生成前报价 |
| 音乐 | 选起点、音量，自动淡入淡出 |
| 音效 | 按时间点放入，音效响起时自动压低音乐 |
| 检查 | 不看片也能核对：尺寸、每秒音量、画面卡顿、缩略图 |

运行 `python3 scripts/build.py --list` 可以看到全部特效和转场的名字。

## 自动字幕（可选）

```bash
pip install faster-whisper
python3 scripts/captions.py 口播.mp4 --out captions.json --srt 口播.srt --hint "品牌名, WhatsApp"
```
然后在项目文件里加上 `"captions": {"file": "captions.json", "anim": "highlight"}`。
第一次运行会下载语音模型（默认 `small`，约 0.5 GB）。品牌名、人名容易听错：用 `--hint` 提前告诉它，剩下的错字用 `--fix "错=对"` 改。发布前请读一遍字幕。

## 品牌片头片尾（可选）

```bash
npx hyperframes telemetry disable      # 可选：不向 HeyGen 发送使用统计
python3 scripts/motion.py intro.mp4 --title "BrandUp Academy" --kicker "AI VIDEO LAB" --subtitle "Learn AI. Create better content."
```
也可以直接写进项目文件的镜头里：`{"motion": {"title": "...", "kicker": "...", "subtitle": "..."}, "dur": 3}`，见 `examples/motion_project.json`。
需要 Node.js 22+、ffprobe 和网络。详见 [docs/RESOURCES.md](docs/RESOURCES.md)。

## 一句话做广告

```bash
python3 scripts/ad.py recipes                          # 看有哪些广告配方
python3 scripts/ad.py new "帮我的冷萃咖啡做一条 15 秒广告" --recipe product_showcase_15s --dir ads/kopi
python3 scripts/ad.py check ads/kopi                   # 检查方案，列出还要生成什么、大约多少 Sparks
python3 scripts/ad.py build ads/kopi                   # 出片；还没生成视频的镜头先用分镜图顶上
```

流程是：一句话加两三个问题 → AI 助手按配方写出分镜和文案（`plan.json`）→ 先生成便宜的分镜图，出一条预览片给你确认
→ 确认并同意费用后再生成视频、配乐、配音、音效 → 自动剪好并检查。
`examples/ad_example/` 是一份写好的示例方案。`scripts/ad.py` 自己不会花任何额度，生成由你或 AI 助手在 Bloomway 里完成。

配方在 `recipes/`，是通用的广告结构，可以改成你自己的。品牌资料照 `brand.example.json` 写一次，之后每条广告自动套用。
`prices.example.json` 里是示例价格，请按 Bloomway 当前显示的价格修改。

## 它不是什么
它不是 CapCut：没有界面、没有时间线预览、没有贴纸模板、没有关键帧动画、没有美颜和抠像。
选哪个镜头、放在哪一秒，要你或 AI 助手来决定；它负责把决定准确地执行出来，并且可以重复执行。

## 安装
需要 Python 3.9+。FFmpeg 会随 `imageio-ffmpeg` 自动装好。

**作为 Claude Code skill 安装（推荐）**
```bash
# Mac / Linux
git clone https://github.com/brandup-academy/cutkit-ai.git ~/.claude/skills/promo-video-editing
# Windows (PowerShell)
git clone https://github.com/brandup-academy/cutkit-ai.git "$env:USERPROFILE\.claude\skills\promo-video-editing"
```
以后更新：在那个文件夹里运行 `git pull`。

**安装依赖**
```bash
pip install pillow numpy imageio-ffmpeg
pip install faster-whisper   # 只有自动字幕需要
```
品牌片头片尾另外需要 Node.js 22+ 和完整的 FFmpeg（含 ffprobe）。
已经装了 ffmpeg 就不需要 `imageio-ffmpeg`。也可以用环境变量 `FFMPEG` 指定 ffmpeg 的路径。

## 三分钟上手
```bash
python3 scripts/selftest.py
```
这条命令会生成一套无版权的练习素材，做出一条 8 秒竖屏视频，并自动核对结果。成片在 `examples/out/demo_9x16.mp4`。

```bash
python3 scripts/build.py examples/fx_project.json
```
这条做出横屏的特效和转场演示，成片在 `examples/out/fx_16x9.mp4`。

## 文件
| 文件 | 作用 |
|---|---|
| `scripts/ad.py` | 一句话广告：建方案、检查和报价、出片 |
| `scripts/build.py` | 一键成片 |
| `scripts/anim_text.py` | 动态文字 |
| `scripts/captions.py` | 自动字幕（可选） |
| `scripts/motion.py` + `motion/` | 品牌片头片尾（可选，HyperFrames） |
| `scripts/check.py` | 检查成片 |
| `scripts/make_card.py` | 单独画一张字幕卡 |
| `scripts/mix_sfx.py` | 给已有视频加音效 |
| `scripts/cut_clip.py` | 截一段无声片段，拿去 AI 工具生成音效 |
| `scripts/find_offset.py` | 找出录屏和原片之间的错位 |
| `docs/TUTORIAL.md` | 分步教程 |
| `docs/PROJECT_FORMAT.md` | 项目文件的全部选项 |
| `docs/RESOURCES.md` | 可以另外安装的工具：配音、网页设计、动态图形 |
| `recipes/` | 广告配方 |
| `brand.example.json` / `prices.example.json` | 品牌资料和价格表的示例 |
| `rules/general.md` | 通用剪辑规则 |
| `rules/my-preferences.example.md` | 个人偏好的写法示例 |
| `AGENTS.md` / `SKILL.md` | 给 Codex / Claude Code 的说明 |

## 已知范围
- 在 macOS、ffmpeg 7.1、Python 3.9 上测试过。脚本是纯 Python，没有 shell 脚本。
- Windows 和 Ubuntu：每次推送代码，GitHub Actions 会用 Python 3.11 自动运行自测 `scripts/selftest.py`，做出 8 秒演示片、动态文字示例和一句话广告示例，并核对尺寸、时长和声音。自动字幕和品牌片头片尾不在这项自动测试里；Windows 和 Linux 上目前只有这一项测试。
- 动态文字和所有脚本都是本仓库自己的代码，只依赖 Pillow、numpy 和 ffmpeg，没有打包第三方程序。
- 品牌片头片尾调用 [HyperFrames](https://github.com/heygen-com/hyperframes)（Apache-2.0），通过 `npx` 在运行时下载，仓库里不包含它。
- 自动字幕调用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)（MIT），需要另外安装，仓库里不包含它和语音模型。
- 字体不随仓库提供。不指定时会找系统里的字体；请使用你有权使用的字体。
- `check.py` 是测量，不是试听。发布前请自己播放一遍。

### What is tested

Tested on macOS with ffmpeg 7.1 and Python 3.9. On every push, GitHub Actions also runs the self-test (`scripts/selftest.py`) on Windows and Ubuntu with Python 3.11: it builds the 8-second demo, the animated-text example and the one-sentence ad example, then checks size, length and sound.
Auto subtitles and the brand intro/outro are not part of that automated run, and it is the only testing done on Windows and Linux so far.

## 配合 Bloomway 使用

这个工具包负责"剪"。画面、音乐和音效可以用 [Bloomway](https://bloomway.ai/?ref=BWUF5CQXX) 生成，镜头可以先用 Bloomway 开源的 [World Director](https://github.com/bloomway-ai/bloomway-world-director) 预演。

| 步骤 | 用什么 | 产出 |
|---|---|---|
| 1. 预演 | [Bloomway World Director](https://github.com/bloomway-ai/bloomway-world-director)（开源，MIT），可以[直接在浏览器里试](https://bloomway-ai.github.io/bloomway-world-director/) | 低模场景、角色走位、镜头路径 |
| 2. 生成画面和音乐 | [Bloomway](https://bloomway.ai/?ref=BWUF5CQXX) 网页工作台，或通过 MCP 让 AI 助手调用 | 每个镜头的视频、配乐 |
| 3. 生成音效 | `scripts/cut_clip.py` 截 6 秒无声片段，交给 Bloomway 的视频生成音效 | 和画面对得上的音效 |
| 4. 成片 | `scripts/build.py` 一个项目文件出片，`scripts/check.py` 检查 | 9:16 或 16:9 成片 |

World Director 做的是预演用的低模画面，不是最终成片；最终画面在 Bloomway 里生成。使用 Bloomway 生成的内容请遵守 Bloomway 的使用条款。
本页的 Bloomway 链接是 BrandUp 的推荐链接，通过它注册，你的价格不变。

**案例：** [BLOOMWAY RUN](https://bloomway-run.vercel.app) 是一个能玩的 AI 电影游戏，画面和配乐由 Bloomway 生成，宣传片用这套流程剪辑和配音效。

### Using it with Bloomway

This toolkit does the editing. Footage, music and sound effects can come from [Bloomway](https://bloomway.ai/?ref=BWUF5CQXX); shots can be planned first in Bloomway's open-source [World Director](https://github.com/bloomway-ai/bloomway-world-director) (MIT, [try it in the browser](https://bloomway-ai.github.io/bloomway-world-director/)).

1. **Previs** in World Director: blockout world, character blocking, camera paths.
2. **Generate** shots and music in Bloomway, in the web workspace or from an AI assistant over MCP.
3. **Sound effects:** cut a 6 s silent clip with `scripts/cut_clip.py` and run Bloomway's video-to-sound-effect on it.
4. **Assemble** with `scripts/build.py` and verify with `scripts/check.py`.

World Director produces blockout previs, not final footage. Follow Bloomway's terms of use for generated content.
The Bloomway links on this page are BrandUp's referral link; your price is the same.
Example: [BLOOMWAY RUN](https://bloomway-run.vercel.app), a playable AI film game whose visuals and music were generated with Bloomway; its trailers were cut and sound-designed with this workflow.

## 关于

**[BrandUp Academy](https://www.brandupdesignmarketing.com/zh/academy/)** 是马来西亚广告公司 BrandUp Design Marketing 的培训品牌。这家公司为品牌策划、制作并投放 Facebook 与 Instagram 广告，课程由它的教学团队授课。
学院目前只提供线上课程：**AI 视频与剧情短片大师课**（2 小时，线上，US$25），附学员版课件 PDF 与 Prompt 模板。课程内容见[课程页面](https://www.brandupdesignmarketing.com/zh/academy/#courses)。这个工具包是 [AI 广告工具包](https://www.brandupdesignmarketing.com/zh/academy/ai-tools/)流程里"自动剪辑"那一步的开源工具。

**[BrandUp Academy](https://www.brandupdesignmarketing.com/academy/)** is the training brand of BrandUp Design Marketing, a Malaysian ad agency that plans, produces and runs Facebook and Instagram advertising for brands. Its courses are taught by the agency's teaching team.
The Academy is online only. Its course is the **AI Video & Short Drama Masterclass** (2 hours, online, US$25), with a student PDF of the slides and prompt templates; the syllabus is on the [course page](https://www.brandupdesignmarketing.com/academy/#courses). This toolkit is the open-source auto-editing step of the workflow on the [AI Ad Toolkit](https://www.brandupdesignmarketing.com/academy/ai-tools/) page.

*Learn AI. Create better content. Grow your brand.*

MIT 许可证 © 2026 BrandUp One Sdn Bhd
