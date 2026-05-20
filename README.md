<div align="center">

# book-workflow.skill

**把一本书变成 Obsidian 里"可读、可批注、可双链"的知识结构。**

> 扔一个 PDF 进去，半天后你得到：中文电子书（带封面）+ 第一人称精读笔记 + 跨章节主题归纳。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![Obsidian](https://img.shields.io/badge/Obsidian-Integrated-purple)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab)](https://www.python.org)

```bash
git clone https://github.com/designservice/book-workflow.skill ~/.claude/skills/book-workflow
```

[做什么](#做什么) · [怎么用](#怎么用) · [产物长什么样](#产物长什么样) · [核心机制](#核心机制) · [个人偏好](#个人偏好声明) · [跨平台](#跨平台)

</div>

---

## 做什么

| 线 | 产物 | 时间 | 何时跑 |
|---|---|---|---|
| 🔁 **A · 全本翻译** | 并行 subagent + Calibre/Pandoc → epub / pdf / docx（带封面 + 中文衬线 + A5 + 自动目录） | 1-3 小时（取决于书长 + API 速度） | 可选 |
| 📖 **B · 章节精读** | 进 Obsidian 的逐章 markdown：作者本人**第一人称**中文复述 + 嵌入式短引文（中英对照）+ 编辑解读 + 批注区 | 5-15 min / 章 | 核心 |
| 🌐 **C · 主题归纳** | 全书完成后扫所有章节精读，产出跨章节主题笔记（双链回章节） | 30-60 min | 线 B 完成后 |

**典型组合**：

- 外文书 + 全本中译 → **A + B + C**
- 外文书只要笔记不要翻译 → **B + C**
- 中文书 → **B + C**（不需要 A）
- 想批量翻译以后再读 → 只 **A**

---

## 怎么用

### 装

```bash
git clone https://github.com/designservice/book-workflow.skill \
  ~/.claude/skills/book-workflow

# 线 A 必需（不跑 A 可跳过）
brew install --cask calibre
brew install pandoc

# 通用 Python 解析
python3 -m pip install -r ~/.claude/skills/book-workflow/requirements.txt
```

### 跑

在 Claude Code 里：

```
/book-workflow /path/to/book.pdf
```

或自然语言：`帮我读这本书 /path/to/book.pdf`

Skill 一次问完 8 个参数：跑哪几条线、目标语言、vault 路径、章节笔记详略、并行度等。所有参数写进 `.book-workflow.json` 支持断点续跑。

---

## 产物长什么样

```
~/Documents/Obsidian/Vault/书库/<原书主标题>-<作者姓>/
├── index.md                       ← 书的总入口（所有章节 + 产物链接）
├── CLAUDE.md                      ← 给 AI 看的本书上下文
├── 00_全本中译/                   ← 线 A 产物
│   ├── 01_前言_*.md ...
│   ├── 04_第00章_<标题>.md
│   ├── 05_第01章_<标题>.md
│   ├── 06_第1部_<部标题>.md       ← part 扉页只有标题
│   ├── 07_第02章_<标题>.md ...
│   ├── glossary.json              ← 人名/地名/术语统一译法
│   └── 其他格式/
│       ├── <书名>.epub            ← 带封面 + 中文衬线 + 章节换页
│       ├── <书名>.pdf             ← A5 + 页码 + 自动目录
│       ├── <书名>.docx
│       ├── <书名>.md              ← 合并完整 markdown
│       ├── book-style.css         ← 排版样式（可改）
│       └── images/                ← 原书图片
├── 01_章节精读/                   ← 线 B（镜像 00_全本中译 结构）
│   ├── 00_章节地图.md             ← 进度追踪 + part 分组
│   └── NN_第NN章_<英文 slug>.md ...
└── 02_主题笔记/                   ← 线 C
    ├── index.md
    ├── 方法论_*.md
    └── 人物_*.md
```

文件名规则：`NN_第NN章_xxx.md`（章节）/ `NN_第N部_xxx.md`（part 扉页）。`NN_` 是阅读顺序前缀——这是**最可靠的排序方式**，不依赖任何 Unicode 字典序的巧合。

---

## 核心机制

### Line A · 并行翻译流水线

复用 [deusyu/translate-book](https://github.com/deusyu/translate-book)：

```
PDF
  ↓ Calibre ebook-convert
HTMLZ
  ↓ extract + chunkify
chunks (每块 ~6000 字符)
  ↓ 抽样 5 块 → 主 agent 建 glossary（人名/地名/术语）
  ↓ 8 个 subagent 并行翻译，每 subagent 1 块（fresh context 防截断）
  ↓ 每批合并 sub-agent 术语发现 → glossary
  ↓ manifest SHA-256 校验完整性
  ↓ pandoc merge → ebook-convert
epub + pdf + docx
  ↓ postprocess_book.py
中文章节 markdown + 带封面 epub/pdf
```

`scripts/postprocess_book.py` 一条命令完成：清洗伪方括号 / PDF 首字下沉伪影 / 按 `##` 切章节 / 挪图 / 复制 CSS / 自动挑封面 / 重新生成带 CSS 的 epub + A5 PDF + docx / 全部用中文书名命名。

### Line B · 第一人称中文精读

不写"作者说"，写"作者用中文说"。SKILL.md 里硬约束的写作风格规范：

| # | 规则 |
|---|------|
| 1 | 用**作者本人**的第一人称视角中文复述章节脉络 |
| 2 | 语言风格紧贴原作者——直白、具体、句中有物（名字、数字、地点、时间） |
| 3 | 章节小标题用章节内**具体物件/场景**（"三明治"、"163 英里"、"无花果酱"），**禁止**"核心论点 / 与全书主题的关联"等学术抬头 |
| 4 | 嵌入式精译每章 6-10 处：原文短句 + 中文对照 + 页码 |
| 5 | **不写**"为什么挑这段"前缀；原文嵌入后直接接叙事 |
| 6 | `编辑解读` section 描述书中内容/补充背景，**不评论作者技巧** |
| 7 | 不写元注释（"以下是我以第一人称复述"这种） |
| 8 | `<!-- HUMAN -->` 块留给用户手写 |

### Line C · 主题归纳

线 B 完成后扫所有章节精读 → 识别反复出现的主题 → 每个主题产出：核心命题 → 来自的章节（短引用 + 双链）→ 提炼原则 → 双链相关主题。

---

## 个人偏好声明

这个 skill 的默认选择**是有意见的**，反映个人审美。想用大概率要 fork 改造。已经写死的选择：

| 维度 | 选择 |
|------|------|
| 章节精读叙述视角 | 作者本人**第一人称**（不用"他说"） |
| 章节小标题来源 | 章节内**具体物件**，禁用抽象学术词 |
| 编辑解读 section 名 | "编辑解读"而非"我的解读"（因为 AI 写的不是用户写的） |
| 文件命名 | `NN_第NN章_xxx.md` / `NN_第N部_xxx.md` |
| Part 扉页 | 平级文件，不用文件夹（适配 Obsidian 默认排序） |
| Vault 结构 | `书库/ + 主题/`，没有日记/灵感/项目 |
| Book root index | 单文件汇总所有产物 |

不喜欢的请 fork。

---

## 跨平台

| 部分 | Claude Code | Codex / Cursor / 其他 |
|------|-------------|----------------------|
| `scripts/*.py` | ✅ | ✅ 命令行直接调用 |
| `templates/*.md` | ✅ | ✅ 纯模板 |
| `SKILL.md` 编排 | ✅ | ⚠️ 引用 `Agent` / `AskUserQuestion` / `TaskCreate` 等 CC 特有工具，需翻译成对应平台等价物 |

---

## 工程踩坑日志（写在 SKILL.md 的 `失败处理` section）

这些坑都已经踩过、修过、固化进 skill：

- ❌ 用户清完 temp 后重跑 pandoc → 发现 epub/pdf 没图。**修**：先把 `temp/images/` 挪到 `00_全本中译/其他格式/images/`，再清 temp
- ❌ 翻译 subagent 把章节大标题降级成普通段落 → 切章节时丢章。**修**：postprocess 用 PDF outline 对照 `##` 数量，差距过大时报警
- ❌ Calibre HTMLZ 转 markdown 时段落被 `[文本]` 包裹（伪 markdown 链接残留）。**修**：`strip_pseudo_brackets()` 保留真链接，去伪
- ❌ PDF 首字下沉变成段首孤立字符（"W 在我研究..."、"【【【采】】】访..."）。**修**：`clean_dropcaps()` 处理三种模式
- ❌ Part 扉页当成独立章节会产生 4 个 0KB 假章节。**修**：Part 用 `部分_*.md` 前缀，不占章号
- ❌ Obsidian 文件夹默认聚顶，靠 Unicode 字典序排不准。**修**：所有文件加 `NN_` 数字前缀

---

## 致谢

整合了以下三个开源项目：

| 项目 | 用途 | License |
|---|---|---|
| [deusyu/translate-book](https://github.com/deusyu/translate-book) | 并行 subagent 翻译流水线 | MIT |
| [hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill) | 多格式文本提取（PDF/EPUB/MOBI/TXT） | 见仓库 |
| [alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) | Obsidian + Claude Code 方法论（CLAUDE.md + index.md 模式） | 公开分享 |

本项目 MIT（见 [`LICENSE`](LICENSE)），上游 LICENSE 在 `LICENSE-translate-book` 和 `LICENSE-book-reader`。

---

<div align="center">

MIT License © designservice

</div>
