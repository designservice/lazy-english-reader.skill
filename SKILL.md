---
name: lazy-english-reader
description: Use when the user wants to process a whole book file (PDF, EPUB, MOBI, DOCX, or TXT) into any of — a full Chinese translation, chapter-by-chapter intensive reading notes (第一人称中文复述 + 嵌入式精译 + 编辑解读), an Obsidian reading vault, or cross-chapter theme notes. Trigger even when the user only mentions one of these (translation, reading notes, vault, 主题归纳) — the skill treats them as three independent products (全本翻译 / 章节精读 / 主题归纳) and only runs what's asked. Common trigger phrases include "translate this book", "read this book for me", "make reading notes", "整本翻译", "帮我读这本书", "做精读笔记", "整理到 Obsidian", "读这本英文书".
---

# Lazy English Reader Skill

整书学习工作流。它把 PDF/EPUB/MOBI/DOCX/TXT 拆成三个独立可选的产物：**全本翻译**、**章节精读**、**主题归纳**，外加 Obsidian vault 集成。三个产物可单独跑也可组合跑。

本 skill 是 agent-agnostic 的。文档里出现的 `Read`、`Write`、`Bash`、`Agent`、`AskUserQuestion` 等名称只是能力示例；非 Claude Code 环境映射到等价工具即可。

**来源归属**：
- 全本翻译流水线脚本：[deusyu/translate-book](https://github.com/deusyu/translate-book) (MIT)
- 章节提取脚本：[hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill)
- Obsidian vault 架构方法论：[alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book)

## 三个产物

| | **全本翻译** | **章节精读** | **主题归纳** |
|---|---|---|---|
| 目的 | 整本中译，备查 | 主动学习与吸收 | 全书读完后的横向抽取 |
| 工具 | Calibre + Pandoc + 并行 worker | extract_book.py + 笔记编排 | 扫描章节笔记 + Obsidian 双链 |
| 产物 | epub / pdf / docx / md | 每章一份 markdown：第一人称叙事 + 嵌入式精译 + 编辑解读 | 方法论、人物、概念等主题笔记 |
| 依赖 | `ebook-convert` `pandoc` | 仅 Python 解析库 | 章节精读完成后的章节笔记 |

## 工作流总览

```
Phase 0  收集参数（交互）
Phase 1  环境检查 + vault 准备
Phase 2  全本翻译启动（如选）→ 后台跑
Phase 3  章节结构提取结构 → 生成 MOC + 章节地图
Phase 4  章节循环（前台，按用户节奏）
Phase 5  主题归纳（章节精读全部完成后）
Phase 6  全本翻译完成后挂进 vault
Phase 7  最终报告
```

## Agent 能力映射

执行时只需要：读写文件、运行 shell、搜索文件、向用户收集参数、必要时并行或后台处理 chunk。若平台没有并行 worker，全本翻译可以顺序执行，只是更慢；若没有结构化提问工具，就先让用户提供配置，再写入 `.lazy-english-reader.json`。

**`{baseDir}` 表示这个 skill 的安装目录**——Claude Code 下通常是 `~/.claude/skills/lazy-english-reader/`，其他 agent 请替换成本地实际路径。详细的能力名 → 平台工具映射见 `references/agent_adapter.md`。

## Phase 0 — 收集参数

一次问完以下参数。在 Claude Code 里可用 `AskUserQuestion`；其他 agent 可用自然语言追问、表单、配置文件或等价的用户输入机制。

1. **书的路径**（必填）
2. **跑哪些产物**：只做全本翻译 / 只做章节精读 / **全本翻译 + 章节精读（推荐，主题归纳会在章节精读完成后自动跑）** / 只重跑主题归纳
3. **目标语言**：默认 `zh`
4. **Obsidian vault 路径**：默认 `~/Documents/Obsidian/Vault`
5. **书的笔记目录名**：按 **`<原书主标题>-<作者姓>`** 命名规则推断。规则：
   - 用原书主标题（去掉副标题如 `: Researching, Interviewing, Writing`，去掉冠词 `The/A`，但 `The` 是书名核心一部分时保留）
   - 用 `-` 连接作者姓（last name 或中文姓）
   - 原书是英文 → 用英文（`Moby-Dick-Melville`、`War-and-Peace-Tolstoy`）
   - 原书是中文 → 用中文（`活着-余华`、`人类简史-Harari`）
   - 多字标题用下划线或保留空格替成 `-`（`Brothers-Karamazov-Dostoyevsky`）
6. **章节笔记体量**（不卡死，给 AI 一个参考量级）：
   - **单人章节**（一篇前言 / 一位采访对象）：1500–2500 字中文
   - **多人章节**（3–6 位口述者）：3000–6000 字中文
   - **巨型多人章节**（10+ 位口述者，如 某口述史经典的13 人）：主推 5–6 位主角，其他人在编辑解读里整合，不要硬把每个人拉成同等长度
   - **跟原书章节差不多长**（用户想要逐句中文复述）：选这个时跳过"嵌入式精译"，整章直接当翻译做
7. **全本翻译并行度**：默认 8

把参数写入 `<vault>/书库/<book_dir>/.lazy-english-reader.json` 作为本次 run 的配置档。兼容旧项目时，如果只发现 `.book-workflow.json`，先读取旧文件，再在下次保存时迁移到新文件名。

## Phase 1 — 环境检查 + vault 准备

```bash
python3 --version
which ebook-convert pandoc   # 全本翻译才需要
python3 -m pip install -r {baseDir}/requirements.txt
```

vault 骨架（**仅 vault 不存在时建**，不要覆盖用户已有内容）：

```
<vault>/
├── CLAUDE.md            ← 用 templates/vault_CLAUDE.md（AI context file）
├── index.md             ← 用 templates/vault_index.md
├── 书库/
│   └── <book_dir>/
│       ├── CLAUDE.md    ← 用 templates/book_CLAUDE.md（AI context file）
│       ├── index.md     ← 用 templates/book_index.md
│       ├── 00_全本中译/
│       ├── 01_章节精读/
│       └── 02_主题笔记/
└── 主题/
```

> **重要**：vault 根**不要**自动建 `日记/`、`灵感/`、`项目/` 之类，除非用户明确要做综合性第二大脑。本 skill 默认 vault 是读书笔记专用。

## Phase 2 — 全本翻译启动（后台）

如果用户选了全本翻译：

```bash
mkdir -p <vault>/书库/<book_dir>/00_全本中译/
cd <vault>/书库/<book_dir>/00_全本中译/
python3 {baseDir}/scripts/convert.py "<book_path>" --olang "<target_lang>"
```

之后按全本翻译的 7 步流程（与原 translate-book 一致）：discover chunks → build glossary → parallel worker translate → merge meta per batch → verify → translate title → merge_and_build。

**全本翻译可以后台跑**。Claude Code 可用 `Bash run_in_background=true`；其他环境用后台 shell、任务队列或独立 worker。用户同时要全本翻译和章节精读时，先启动全本翻译再进 Phase 3——这样翻译在后台跑的同时用户可以读章节精读。

> 注：78+ chunks 时建议让全本翻译跑独立长任务，不要在主对话里逐个创建 worker —— 会爆 context。可考虑：
> 1. 写一个独立 shell 脚本调用 claude CLI 顺序翻译，后台 nohup 起
> 2. 或让一个 dispatching worker 内部并行

### 启动同时必须写 HANDOFF.md（防止"翻译跑完没人接"）

后台翻译可能跑 30 min – 2 小时，期间主对话可能完全结束、用户关电脑、几小时后才回来。**启动翻译的同一刻必须立刻**做两件事：

**1. 写 `<vault>/书库/<book_dir>/HANDOFF.md`**，内容样板：

```markdown
# 全本翻译后台任务

- **PID**：`<pid>`（也写到 `/tmp/<book_dir>-translate/translate.pid`）
- **日志**：`/tmp/<book_dir>-translate/translate.log`
- **temp 目录**：`/tmp/<book_dir>-translate/<book_filename>_temp/`
- **预计时间**：30 min – 2 小时
- **完成标记**：当 `<temp_dir>/_DONE` 文件出现时，翻译完成

## 翻译完成后必须运行（Phase 6）

```bash
python3 ~/.claude/skills/lazy-english-reader/scripts/postprocess_book.py \
  "<temp_dir>" \
  "<vault>/书库/<book_dir>/00_全本中译" \
  --title "<中文书名>" \
  --author "<作者>"
```

## 进度检查（任何时候都能跑）

```bash
tail -3 <log_path>
ls <temp_dir>/output_chunk*.md 2>/dev/null | wc -l   # 已完成的 chunk 数
test -f <temp_dir>/_DONE && echo "✅ 翻译完成，可以跑 postprocess" || echo "⏳ 还在跑"
```
```

**2. 让后台脚本在结束时 `touch <temp_dir>/_DONE`**——`scripts/convert.py` 或 `merge_and_build.py` 的最后一行加上 `Path(temp_dir / "_DONE").touch()`。这是主对话 / 用户检查是否完成的唯一可靠信号（不要用日志最后一行匹配，会被部分写入糊弄）。

**3. 重入检查**：每次用户重新触发 `lazy-english-reader`，主对话第一件事是检查 `HANDOFF.md` 是否存在、`_DONE` 是否出现——出现就直接跳到 Phase 6。

具体术语表 / merge / build 细节见原 [translate-book SKILL.md](https://github.com/deusyu/translate-book/blob/main/SKILL.md)。

## Phase 3 — 提取章节结构

```bash
python3 {baseDir}/scripts/extract_book.py "<book_path>" \
    -o "<vault>/书库/<book_dir>/.extracted.json"
```

读 JSON 输出，做章节分组：

- **PDF**：优先用 PDF 自带 outline (`fitz.open(...).get_toc()`)。如果没 outline，再用 metadata + 目录页 fallback
- **EPUB/MOBI**：默认按 EPUB 自带的 chapter 划分。**但要做 anthology 检测**——见下
- **TXT**：按章节标记或固定行数

### EPUB anthology 检测（口述史 / 短篇集 / 散文集必做）

很多书 EPUB 文件里的 "chapter" 其实是**编辑分组**，真正的读单元更细。典型例子：

- 某口述史经典：某 EPUB chapter 内含 13 位工人独白，每位工人才是真正的读单元
- 散文集：一个 EPUB chapter 包含多篇散文
- 短篇集：一个 EPUB chapter = 一本子集，下面才是单篇

**检测**：

```python
# Phase 3 提取完后，对 EPUB / MOBI 检查每个 chapter 的内部结构
for chapter in extracted_chapters:
    body = chapter['text']
    # 找全大写或 markdown-style 内嵌标题
    allcaps_sections = re.findall(r'^[A-Z][A-Z0-9 ,\'\-]{4,}$', body, re.MULTILINE)
    bold_sections = re.findall(r'^\*\*[A-Z][^*]+\*\*$', body, re.MULTILINE)
    if len(allcaps_sections) + len(bold_sections) >= 3:
        # 这个 EPUB chapter 是 anthology，按内部 section 重切
        flag_for_resplit(chapter)
```

**处理**：检测到 anthology 后，**章节笔记单元改成 section（或 worker / 篇）而不是 EPUB chapter**。文件命名仍按阅读顺序数字前缀 `NN_第XX章_<slug>.md`，但"章"现在指的是真正的读单元——可能比 EPUB 自带的 chapter 多很多（该口述史 EPUB 有 ~9 个 chapter，重切后有 29 个真正的读单元 / section）。

这件事**章节精读关心，全本翻译不关心**——全本翻译按 EPUB 自己的 chapter 翻译就行。两条线**章节计数会对不上**，这是正确的；不要为了对齐去强行合并章节精读。

产出 `01_章节精读/00_章节地图.md`：

```markdown
# 章节地图 — <书名>

| # | 章节 | 英文标题 | 页 | 状态 | 链接 |
|---|------|---------|----|------|------|
| 0 | 引言 | Introduction | 1–12 | ⬜ | [[第00章_Introduction]] |
| 1 | ... | ... | ... | ⬜ | [[第01章_xxx]] |
```

**不再创建每章子目录**。章节笔记本身将在 Phase 4 直接作为平铺单文件创建，文件名格式 `第NN章_<英文 slug>.md`。

## Phase 4 — 章节循环

**核心规范**：

```
01_章节精读/
├── 00_章节地图.md
├── 第00章_Introduction.md     ← 一章一文件，平铺
├── 第01章_xxx.md
├── ...
```

每章一个 markdown，**单文档**，结构如下：

```markdown
---
book: "<书名 — 作者>"
chapter: N
chapter_title: "中文标题 / 英文标题"
pages: [start, end]
status: draft | done
voice: 第一人称（作者自述，中文复述）
tags: [...]
created: YYYY-MM-DD
---

# 第 N 章 — 中文章名 / English Title

## [具体物件/场景小标题 1]

[第一人称中文叙述]

> 中文译文（关键的一两句，作者本人有强语气 / 动作 / 细节的瞬间）
> *English original here* (p.XX)

[继续叙述]

## [小标题 2]
...

---

## 编辑解读

> 笔记整理者（非作者）的几条说明，**描述书中内容/补充背景**，不评论作者技巧。

**关于 XXX。** ...

**关于 XXX。** ...

---

## 我的批注

<!-- HUMAN -->

<!-- /HUMAN -->

---

## 链接

- ↑ [[00_章节地图]]
- ← 上一章：[[第NN章_xxx]]
- → 下一章：[[第NN章_xxx]]
- 关联主题：[[../02_主题笔记/...]]（待写）
```

### 章节 vs 部分（重要区分）

> PDF outline 里 part 扉页 vs 真章节怎么区分、文件命名 `第N部_xxx.md` / `第NN章_xxx.md` 怎么排前缀、全本翻译/章节精读 怎么镜像——详细规则和 *War and Peace* 等典型例子见 `references/chapters_vs_parts.md`。处理 PDF outline 出现 L1/L2 混合时必读。

### Book 目录入口 = book root index.md（不要在 00_全本中译/ 里再加 index）

每本书的入口是 **`书库/<book_dir>/index.md`**，不在 `00_全本中译/` 再起一个 index。这一个文件包含：

- 章节表（按 part 分组，每行：中文译本链接 + 精读笔记链接）
- 中文版下载（epub/pdf/docx 链接到 `00_全本中译/其他格式/`）
- 主题笔记链接（主题归纳产物）
- 术语表链接
- 元信息

`01_章节精读/00_章节地图.md` 仍然保留——它是章节进度追踪表，可以在 book root index 里链过去。

### 写作风格规范（写每一章都必须遵守）

> 写每一章前先读 `references/writing_style.md` —— 全部强制规则（第一人称、小标题取自具体物件而非"核心内容/主要论点"、**中文 primary 英文小字辅助**、跨文化抽象词必须 inline gloss、编辑解读边界、不写元说明等）。这些规则不遵守会让笔记直接变成"读书报告体"，丧失这个 skill 的核心价值。

> **多人多视角章节**（一个"章"下面有 3+ 位口述者 / 人物 / 案例，如 某口述史经典 的汽车业 13 人）：另外读 `references/multi_worker_chapter.md` 用专门的模板（H2 = 人物 + H3 = 物件 / 动作小标题 + 章末统一编辑解读）。

### 循环节奏（强制使用 subagent 派发）

**为什么必须 subagent**：每章笔记 3000–6000 字中文 + 嵌入式精译 + 读源章节，光做一章主对话就要消耗 10K+ tokens。30 章的书在主对话里直接做，主对话上下文撑不到 10 章就会枯竭——AI 会自己说"context 快不够了"然后停下。这个 skill 在真实测试中**只靠运气拐回 subagent 模式才完成**。新跑必须从第 2 章开始就强制走 subagent。

**节奏**：

1. **第 1 章**：主对话直接做（Read 源章节 + Write 章节笔记）。**做完停下来**——给用户看风格样本，等用户确认 / 反馈。这一章是风格基准，反馈很关键。
2. **第 2 章起**：每章一个 `Agent` 子任务，**主对话只调度不读章节内容**。每个 subagent 拿到的 prompt 必须自包含，含：
   - 源章节文件路径（agent 自己去读）
   - `{baseDir}/references/writing_style.md`（写作 9 条规则）
   - `{baseDir}/references/multi_worker_chapter.md`（多人多视角章节模板，如适用）
   - 章节元数据（章号、英文标题、中文标题、页码范围）
   - 输出路径（`01_章节精读/NN_第XX章_xxx.md`）
   - 上 / 下一章的文件名（用于双链）
   - 第 1 章作为风格样本的文件路径（让 subagent 对照风格）
3. **并行度**：一次 8–10 个 subagent 并行。每批完成后更新 `00_章节地图.md`，向用户汇报 N 章 ✅，征求继续 / 改风格 / 暂停。
4. **从第 1 章主对话 → 第 2 章 subagent 是硬切换**。不要"第 2 章再主对话试一下"——主对话每多做一章，剩余 budget 就少一截。

**收益**：用户实测 某口述史经典（29 章）— 前 9 章主对话直接做几乎耗尽主对话 context，后 20 章 + 7 篇主题笔记换成 subagent 并行派发，主对话 context 节省 ≥70%。

## Phase 5 — 主题归纳

章节精读全部完成后，扫描所有章节精读文件的"编辑解读"和小标题，识别反复出现的主题，为每个主题产出一份笔记到 `02_主题笔记/`：

```
02_主题笔记/
├── index.md
├── 方法论_xxx.md
├── 人物_xxx.md
```

每份主题笔记：
- 跨章节聚合相关段落（双链回章节）
- 提炼 3-5 条原则/金句
- 链到 `<vault>/主题/` 下的跨书概念笔记（如果存在）

同时更新 `<vault>/主题/` 跨书笔记。

## Phase 6 — 全本翻译完成后挂进 vault

**入口**：检查 `<temp_dir>/_DONE` 是否存在（见 Phase 2 的 HANDOFF 机制）。如果存在，立刻跑下面的命令；如果不存在，说明翻译还在跑，**不要尝试 postprocess**——会读到半成品。直接告诉用户"翻译还在跑，预计 X chunks 剩余"。

如果用户重新触发 skill 而当时翻译刚好跑完，主对话第一件事就是检查 `_DONE` → 跑 postprocess。**不要把这一步留给用户记得去手动跑**——这是上一版 skill 真实测试中翻译跑完没人接的根因。

```bash
python3 {baseDir}/scripts/postprocess_book.py \
    "<temp_dir>" \
    "<vault>/书库/<book_dir>/00_全本中译" \
    --title "<中文书名（不带《》）>" \
    --author "<作者>"
```

这条 **一条命令完成所有后处理**：

```bash
python3 {baseDir}/scripts/postprocess_book.py \
    "<temp_dir>" \
    "<vault>/书库/<book_dir>/00_全本中译" \
    --title "<中文书名（不带《》）>" \
    --author "<作者>"
```

这个脚本做了：

1. 读 temp dir 的 `output.md`，**清洗伪方括号** `[文本]`（Calibre HTMLZ → markdown 的伪影），保留真链接和图片
2. 按 `##` 标题**切分**成每章独立 markdown，**平铺**在 `00_全本中译/` 根
3. 把 temp dir 的 `images/` **挪到** `00_全本中译/其他格式/images/`
4. 复制 `glossary.json` 到 `00_全本中译/`
5. 复制 `templates/book-style.css` 到 `其他格式/book-style.css`
6. 用 PIL 自动**挑封面图**（第一张高 > 1000px 的竖版 JPG），用 pandoc 重新生成带封面 + 中文 CSS 的 epub
7. 用 ebook-convert 把 epub 转成 **A5 + 页码 + 自动目录 + 章节换页**的 PDF
8. 用 pandoc 生成带标题/作者/目录的 docx
9. 所有产物用**中文书名**命名（`<书名>.epub` / `.pdf` / `.docx` / `.md`），不用 `book.*`
10. 删除 temp dir（`--keep-temp` 可保留）

最终布局：

```
00_全本中译/
├── index.md            ← 由协调 agent 在 Phase 6 之后写
├── glossary.json
├── 00_xxx.md … NN_xxx.md  ← 每章独立 markdown
└── 其他格式/
    ├── <书名>.epub
    ├── <书名>.pdf
    ├── <书名>.docx
    ├── <书名>.md       ← 合并后的完整 markdown
    ├── book-style.css
    └── images/         ← 原书图片
```

然后协调 agent 写 `00_全本中译/index.md`（用 Obsidian 双链列出所有章节 + `其他格式/` 入口），并在 book_dir 的 `index.md` 顶部加链接。

如果全本翻译失败：在 `00_全本中译/_FAILED.md` 写诊断信息。

## Phase 7 — 最终报告

向用户汇报，按状态分两种情况：

**Case A：所有产物完成**
- 全本翻译产物路径 + 大小
- 章节精读：N 章 ✅，Obsidian 路径，章节地图链接
- 主题归纳：M 篇主题笔记
- 下一步建议（在 Obsidian 读、批注、跨书互联）

**Case B：章节精读 + 主题归纳完成，全本翻译还在后台跑**

写一份 `<vault>/书库/<book_dir>/REPORT.md` 中期报告（不写 STDOUT 长汇报），结构：
- 已完成的产物（章节精读 + 主题归纳的细目）
- 全本翻译当前进度（X / Y chunks，预计还需 X 小时）
- 引用 `HANDOFF.md` 里的进度检查命令
- 写明：翻译完成后用户再触发一次 `lazy-english-reader`，主对话会自动检查 `_DONE` 并跑 Phase 6

这样用户关电脑去做别的事，几小时后回来重新触发 skill 就能无缝衔接。

## 断点续跑

每个 Phase 可中断重入。**用户重新触发 `lazy-english-reader` 时，主对话第一件事按此顺序检查**：

1. **`<vault>/书库/<book_dir>/HANDOFF.md` 是否存在** → 说明上次启动了后台翻译
   - 如果 `<temp_dir>/_DONE` 已出现 → 跳到 Phase 6 跑 postprocess
   - 如果 `_DONE` 没出现 → 给用户看进度，问"继续等 / 重启 / 杀掉"
2. **`.lazy-english-reader.json` 是否存在**（兼容读取旧的 `.book-workflow.json`） → 拿之前的参数，问用户"延用 / 改一下 / 推倒重来"
3. **`.extracted.json` 是否存在** → Phase 3 可跳过
4. **`01_章节精读/00_章节地图.md` 里 ✅ 状态字段** → Phase 4 只处理未完成的章
5. **`02_主题笔记/index.md` 是否存在** → Phase 5 可跳过

全本翻译自带 chunk-level resume（已有 `output_chunk*.md` 的 chunk 跳过），所以即使后台进程被杀，重启脚本会接上。

## 失败处理

> 各种错误恢复手册见 `references/troubleshooting.md`（Calibre 缺失、扫描版 PDF 要 OCR、chunk 翻译失败、temp/images 清理顺序、pandoc 重跑前备份等）。

## 附录

全本翻译 worker 的翻译 prompt 模板（复用 translate-book）+ 章节标题降级陷阱与对策 + `scripts/realign_headings.py` 设计草稿，全部见 `references/translate_prompt.md`。
