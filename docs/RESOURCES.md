# 课程资源：可以另外安装的工具

这些工具不在本仓库里，也没有被整合进脚本。它们是独立软件，学员按需自己安装。
星数和许可证以 2026 年 11 月在 GitHub 上看到的为准，使用前请再看一次各自的条款。

## 配音：VoiceStudio
- 仓库：https://github.com/debpalash/VoiceStudio
- 是什么：在自己电脑上运行的 AI 配音软件，可以生成配音、做声音克隆、视频配音和转写，支持很多语言。
- 怎么配合本工具：在 VoiceStudio 里生成配音，导出 mp3 或 wav，按 `plan.json` 里每个镜头的 `vo_file` 文件名保存，或在项目文件里作为 `cues` 放入。本工具支持任何来源的配音文件。
- 许可证：AGPL-3.0。可以安装使用；不要把它的代码复制进你自己的项目。如果把它改过之后架成网站或服务给别人用，需要公开改过的源代码。
- 声音克隆：只克隆你自己的声音，或取得本人书面同意的声音。

## 网页设计：Impeccable 和 Hallmark
它们改的是网页，不是视频。适合用来改官网、课程报名页、作品集页面。
- Impeccable：https://github.com/pbakaus/impeccable （Apache-2.0）。命令如 `critique`、`polish`、`bolder`，并能检查"AI 味"的设计。
- Hallmark：https://github.com/Nutlope/hallmark （MIT，Together AI 出品）。50 套主题，主打做出来不像 AI 生成的页面。
两者都装在 Claude Code、Codex 或 Cursor 里使用，按各自 README 安装。

## 动态图形：HyperFrames
- 仓库：https://github.com/heygen-com/hyperframes （Apache-2.0）
- 本工具的 `scripts/motion.py` 用它渲染品牌片头和片尾（可选功能）。
- 需要 Node.js 22+、ffmpeg 和 ffprobe（完整安装 FFmpeg 就会有 ffprobe），第一次运行会自动下载 Chrome 渲染器。
- 模板通过网络加载 GSAP 动画库，所以渲染时需要联网。
- 它默认会向 HeyGen 发送使用统计。不想发送就运行一次 `npx hyperframes telemetry disable`，或设置环境变量 `HYPERFRAMES_NO_TELEMETRY=1`。
- 更多现成的动画模板：https://github.com/heygen-com/hyperframes-launches （Apache-2.0）
