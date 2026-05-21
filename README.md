<div align="center">

# 不想读英文书.skill

<sub>`lazy-english-reader.skill`</sub>

**把英文原版书处理成中文译本、章节精读笔记和 Obsidian 主题索引。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent-Agnostic](https://img.shields.io/badge/Agent-Agnostic-blueviolet)](https://skills.sh)
[![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)
[![Obsidian](https://img.shields.io/badge/Obsidian-Integrated-purple)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab)](https://www.python.org)

```bash
npx skills add designservice/lazy-english-reader.skill
```

[做什么](#做什么) · [怎么用](#怎么用) · [产物长什么样](#产物长什么样) · [亮点](#亮点) · [跨平台](#跨平台)

</div>

---

> 这个 skill 不是替你“读完一本书”，而是把读英文原版前最费力的准备工作做好：翻译、拆章、补背景、整理索引，并把结果放进 Obsidian。你仍然要读，但会更容易读下去，也更容易回头查。

## 做什么

扔一个 PDF 进去，你可以按需要得到三类产物：

| 产物 | 适合什么时候用 | 你要做的 | AI 在后台跑多久 |
|------|----------------|----------|----------|
| 🔁 **全本中文译本** | 想留一份可检索、可导出的中文版本 | 启动后等通知 | 30 min – 2 小时（看书厚度 + 并行度） |
| 📖 **章节精读笔记** | 想真正读懂每一章，并在 Obsidian 里继续批注 | 启动后按自己节奏读 / 批注 | 每章 1–3 min 生成，整本 < 1 小时 |
| 🌐 **主题索引** | 读完整本后，按人物、概念、方法论回看全书 | 启动后等通知 | 10–20 min |

章节精读是核心产物：它会生成作者第一人称中文复述、短句中英对照、必要背景补充，以及留给你自己的批注区。

**常见用法**：

- 英文原版想认真读完，并留中文版本备查：**全本译本 + 章节精读 + 主题索引**
- 只想做读书笔记，不需要完整译本：**章节精读 + 主题索引**
- 中文书也想拆成精读笔记：**章节精读 + 主题索引**
- 只想先做一份中文译本：**全本译本**

---

## 怎么用

### 安装

如果你主要在 Claude Code 里用：

```bash
git clone https://github.com/designservice/lazy-english-reader.skill \
  ~/.claude/skills/lazy-english-reader
```

全本译本导出 epub / pdf 时需要 Calibre 和 Pandoc；只跑章节精读可以先跳过：

```bash
brew install --cask calibre
brew install pandoc
```

安装通用 Python 依赖：

```bash
python3 -m pip install -r ~/.claude/skills/lazy-english-reader/requirements.txt
```

### 跑

在支持 skills 的 agent 里：

```
/lazy-english-reader /path/to/book.pdf
```

或自然语言：`帮我读这本书 /path/to/book.pdf`

Skill 会一次问完必要参数，比如要生成哪些产物、目标语言、Obsidian vault 路径和笔记详略。配置会保存到 `.lazy-english-reader.json`，中途停掉后可以继续跑。

---

## 产物长什么样

默认会在你的 Obsidian vault 里生成一个书籍目录：

```text
~/Documents/Obsidian/Vault/书库/<书名>-<作者>/
├── index.md                 ← 书的总入口
├── CLAUDE.md                ← 给 AI 继续处理这本书时使用的上下文
├── 00_全本中译/             ← 中文译文章节和导出文件
│   ├── *.md
│   └── 其他格式/
│       ├── <书名>.epub
│       ├── <书名>.pdf
│       ├── <书名>.docx
│       └── <书名>.md
├── 01_章节精读/             ← 逐章精读笔记
│   ├── 00_章节地图.md
│   └── NN_第NN章_<标题>.md
└── 02_主题笔记/             ← 全书主题索引
    ├── index.md
    ├── 方法论_*.md
    └── 人物_*.md
```

文件名前面的 `NN_` 用来固定阅读顺序，保证 Obsidian 文件列表按书的顺序排列。

---

## 亮点

这个 skill 不是把一本英文书压缩成几段摘要，而是把它整理成一套可以长期阅读、检索和继续批注的中文读书材料。

### 1. 得到一本真正能读的中文版本

它会把英文原书整理成完整中文译本，并导出 EPUB、PDF、DOCX 和 Markdown。人名、地名、概念会尽量保持一致，避免一本书里同一个术语反复变脸。

### 2. 章节精读更像中文重读，而不是读书报告

章节笔记不会停留在“本章主要讲了三点”。它会用中文保留作者的叙述脉络、语气和推进方式，同时嵌入关键英文原句、中文对照和页码，方便你随时回到原书核对。

### 3. 可以直接放进 Obsidian

每本书都会整理成清晰的目录结构，包括总入口、章节地图、全本中译、章节精读和主题笔记。文件按阅读顺序排列，放进 Obsidian 后可以直接浏览和检索。

### 4. 读完后自动沉淀主题索引

反复出现的人物、概念、方法论会被整理成主题笔记，并反链回相关章节。它更适合做长期知识库，而不是生成一次性的读书摘要。

### 5. 给你的批注留位置

章节笔记会保留个人批注区域。你可以继续写自己的理解、摘录和问题，后续让 AI 补充或改稿时，也不会轻易覆盖你的笔记。

---

## 跨平台

这个 skill 不绑定 Claude Code。仓库里放了几个轻量入口文件，让其他 agent 也能用同一套流程：

| Agent | 入口文件 |
|-------|------|
| Claude Code / skills.sh | `SKILL.md` |
| Codex / OpenAI Codex CLI | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `.cursor/rules/lazy-english-reader.mdc` |

每个入口文件都只有几行，告诉对应 agent 去读 `SKILL.md`。真正的工作流维护在 `SKILL.md` 里。能力名映射（`Bash` / `Read` / `AskUserQuestion` / `Agent` 怎么对应到你这个平台的工具）和 `{baseDir}` 含义统一放在 `references/agent_adapter.md`，所有入口文件都指过去——加新平台时只要复制一个 3 行壳文件，映射表自动复用。

更多 reference 文档（章节标题对齐、写作风格规范、失败处理等）按需加载，平时不进 agent 的 context：

- `references/agent_adapter.md` — 能力名 → 平台工具映射
- `references/writing_style.md` — 章节笔记写作规则（叙事 / 中文化 / 跨文化术语 / 编辑解读）
- `references/multi_worker_chapter.md` — 多人多视角章节模板（口述史 / 短篇集 / 散文集）
- `references/chapters_vs_parts.md` — PDF outline 处理（part 扉页 vs 真章节）
- `references/troubleshooting.md` — 常见错误恢复
- `references/translate_prompt.md` — 全本翻译 prompt + 章节标题对齐

`scripts/*.py` 可以直接命令行调用，`templates/*.md` 和 `templates/*.html` 是 Markdown / Pandoc 模板。生成的 `CLAUDE.md` 是这本书的 AI 上下文文件；如果你的 agent 使用 `AGENTS.md`、`GEMINI.md` 或其他约定，可以复用同一份内容。

---

## 致谢

整合了三个开源项目：

| 项目 | 用途 | License |
|---|---|---|
| [deusyu/translate-book](https://github.com/deusyu/translate-book) | 并行翻译流水线 | MIT |
| [hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill) | 多格式文本提取 | 见仓库 |
| [alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) | Obsidian + Claude Code 方法论 | 公开分享 |

本项目 MIT（见 [`LICENSE`](LICENSE)），上游 LICENSE 在 `LICENSE-translate-book` 和 `LICENSE-book-reader`。

---

<div align="center">

MIT License © designservice

</div>
