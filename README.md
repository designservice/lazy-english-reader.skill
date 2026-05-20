<div align="center">

# 不想读英文书.skill

<sub>`lazy-english-reader.skill`</sub>

**让 AI 替你啃英文原版书：自动翻译 + 拆解成 Obsidian 里的中文精读笔记。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![Obsidian](https://img.shields.io/badge/Obsidian-Integrated-purple)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab)](https://www.python.org)

```bash
git clone https://github.com/designservice/lazy-english-reader.skill ~/.claude/skills/book-workflow
```

[做什么](#做什么) · [怎么用](#怎么用) · [产物长什么样](#产物长什么样) · [核心机制](#核心机制) · [跨平台](#跨平台)

</div>

---

> **不是 AI 替你"读"，是 AI 替你做"读之前的准备工作"**。线 B 的章节精读笔记仍然要求你读——它把英文原版变成中文 + 中英对照 + 编辑解读 + 留批注区，让你**真正能读下去**。

## 做什么

扔一个 PDF 进去，半天后你得到三样东西（都可选）：

| 产物 | 时间 | 何时跑 |
|------|------|--------|
| 🔁 **A · 全本翻译** — AI 把整本英文书翻成中文，自动排版成电子书（封面 + 宋体 + 口袋本大小 + 目录） | 1-3 小时 | 可选 |
| 📖 **B · 章节精读** — 进 Obsidian 的逐章笔记：作者本人**第一人称**中文复述 + 短句中英对照 + 编辑补的背景 + 留你自己批注的位置 | 5-15 min/章 | 核心 |
| 🌐 **C · 主题归纳** — 全书读完后扫所有章节，提炼出跨章节的方法论/人物/概念笔记 | 30-60 min | 线 B 完成后 |

**典型组合**：

- 想啃外文书 + 留一份中文电子书备查 → **A + B + C**
- 只要笔记不要全译本 → **B + C**
- 中文书也想做精读 → **B + C**（不需要翻译）
- 只想做翻译给以后查 → 只 **A**

---

## 怎么用

### 装

```bash
git clone https://github.com/designservice/book-workflow.skill \
  ~/.claude/skills/book-workflow

# 线 A 才需要（不跑 A 可跳过）
brew install --cask calibre
brew install pandoc

# Python 解析库（通用）
python3 -m pip install -r ~/.claude/skills/book-workflow/requirements.txt
```

### 跑

在 Claude Code 里：

```
/book-workflow /path/to/book.pdf
```

或自然语言：`帮我读这本书 /path/to/book.pdf`

Skill 会一次问完 8 个参数（跑哪几条线、目标语言、vault 路径、详略、并行度等），全部存进 `.book-workflow.json` 支持断点续跑。

---

## 产物长什么样

跑完后产物全部在你的 Obsidian vault 里：

```
~/Documents/Obsidian/Vault/书库/<原书主标题>-<作者姓>/
├── index.md                       ← 书的总入口
├── CLAUDE.md                      ← 给 AI 看的本书上下文
├── 00_全本中译/                   ← 线 A 产物
│   ├── 01_前言_*.md ...
│   ├── 04_第00章_<标题>.md
│   ├── 05_第01章_<标题>.md
│   ├── 06_第1部_<部标题>.md       ← part 扉页只标题
│   ├── 07_第02章_<标题>.md ...
│   ├── glossary.json              ← 人名/地名/术语统一译法
│   └── 其他格式/
│       ├── <书名>.epub            ← 带封面 + 中文宋体
│       ├── <书名>.pdf             ← 口袋本大小 + 页码 + 目录
│       ├── <书名>.docx
│       ├── <书名>.md              ← 合并完整 markdown
│       └── images/
├── 01_章节精读/                   ← 线 B 产物（镜像 00_全本中译 结构）
│   ├── 00_章节地图.md
│   └── NN_第NN章_<英文 slug>.md ...
└── 02_主题笔记/                   ← 线 C 产物
    ├── index.md
    ├── 方法论_*.md
    └── 人物_*.md
```

文件名规则：`NN_第NN章_xxx.md`（章节）/ `NN_第N部_xxx.md`（part 扉页）。`NN_` 是阅读顺序前缀——保证 Obsidian 文件列表按阅读顺序排，不靠 Unicode 字典序的巧合。

---

## 核心机制

### Line A · 并行翻译流水线

复用 [deusyu/translate-book](https://github.com/deusyu/translate-book)，加上后处理一步：

```
英文 PDF
  ↓ 拆成 6000 字符一块的小片段
  ↓ AI 先看 5 块抽样建术语表（人名/地名统一译法）
  ↓ 8 个 AI 并行翻译（每个 AI 只处理 1 块，避免上下文污染）
  ↓ 每批结束把新发现的术语合并回总术语表
  ↓ 全部完成后合并 → 排版 → 加封面 → 出电子书
中文电子书 + 按章节切分的 markdown
```

### Line B · 第一人称中文精读

不写"作者说"，写"作者用中文说"。每章 markdown 用作者本人的视角中文复述脉络，关键原文短句以引用块嵌入 + 中文对照 + 页码。

SKILL.md 里的硬约束写作规范：

| # | 规则 |
|---|------|
| 1 | 用**作者本人**的第一人称视角中文复述 |
| 2 | 紧贴原作者语言风格——直白、具体、句中有物（名字、数字、地点、时间） |
| 3 | 章节小标题用章节内**具体物件/场景**，禁止"核心论点 / 与全书主题的关联"等学术抬头 |
| 4 | 嵌入式精译每章 6-10 处：原文短句 + 中文对照 + 页码 |
| 5 | **不写**"为什么挑这段"前缀 |
| 6 | `编辑解读` section 描述内容/补背景，**不评论作者技巧** |
| 7 | 不写元注释（"以下是我以第一人称复述"这种） |
| 8 | `<!-- HUMAN -->` 块留给用户写 |

### Line C · 主题归纳

线 B 完成后扫所有章节，识别反复出现的主题，每个主题产出：核心命题 → 来自的章节（短引用 + 双链）→ 提炼原则 → 双链相关主题。

---

## 跨平台

| 部分 | Claude Code | Codex / Cursor / 其他 |
|------|-------------|----------------------|
| `scripts/*.py` | ✅ | ✅ 命令行直接调用 |
| `templates/*.md` | ✅ | ✅ 纯模板 |
| `SKILL.md` 编排 | ✅ | ⚠️ 引用 `Agent` / `AskUserQuestion` 等 CC 特有工具，需翻译成对应平台等价物 |

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
