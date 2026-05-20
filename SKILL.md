---
name: book-workflow
description: 个人学习用的整书工作流。把一本书（PDF/EPUB/MOBI/DOCX/TXT）处理成两条产物：(A) 全本中译（并行 subagent + Calibre/Pandoc，输出 epub/pdf/docx）和 (B) 进 Obsidian 的逐章精读笔记（第一人称叙事 + 嵌入式精译 + 编辑解读 + 主题归纳）。两条线可独立开关。当用户说"读这本书"、"翻译这本书"、"做读书笔记"、"book-workflow"、"/book-workflow" 时触发。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion, TaskCreate, TaskUpdate
---

# Book Workflow Skill

整书学习工作流。两条独立可选的线，外加 Obsidian vault 集成。

**来源归属**：
- 线 A 翻译流水线脚本：[deusyu/translate-book](https://github.com/deusyu/translate-book) (MIT)
- 线 B 提取脚本：[hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill)
- Obsidian vault 架构方法论：[alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book)

## 两条线

| | 线 A：全本翻译 | 线 B：吸收型笔记 |
|---|---|---|
| 目的 | 整本中译，备查 | 主动学习与吸收 |
| 工具 | Calibre + Pandoc + 并行 subagent | extract_book.py + 笔记编排 |
| 产物 | epub / pdf / docx / md | 每章一份 markdown：第一人称叙事 + 嵌入式精译 + 编辑解读 |
| 依赖 | `ebook-convert` `pandoc` | 仅 Python 解析库 |

## 工作流总览

```
Phase 0  收集参数（交互）
Phase 1  环境检查 + vault 准备
Phase 2  线 A 启动（如选）→ 后台跑
Phase 3  线 B 提取章节结构 → 生成 MOC + 章节地图
Phase 4  线 B 章节循环（前台，按用户节奏）
Phase 5  线 C：主题归纳（线 B 全部完成后）
Phase 6  线 A 完成后挂进 vault
Phase 7  最终报告
```

## Phase 0 — 收集参数

用 `AskUserQuestion` 一次问完：

1. **书的路径**（必填）
2. **跑哪些线**：A only / B only / **A+B（推荐）** / 只重跑 C
3. **目标语言**：默认 `zh`
4. **Obsidian vault 路径**：默认 `~/Documents/Obsidian/Vault`
5. **书的笔记目录名**：按 **`<原书主标题>-<作者姓>`** 命名规则推断。规则：
   - 用原书主标题（去掉副标题如 `: Researching, Interviewing, Writing`，去掉冠词 `The/A`，但 `The` 是书名核心一部分时保留）
   - 用 `-` 连接作者姓（last name 或中文姓）
   - 原书是英文 → 用英文（`Working-Caro`、`Power-Broker-Caro`）
   - 原书是中文 → 用中文（`活着-余华`、`人类简史-Harari`）
   - 多字标题用下划线或保留空格替成 `-`（`Path-of-Power-Caro`）
6. **章节笔记详略**：仅参考用（叙事长度由内容决定，不卡字数）
7. **线 A 并行度**：默认 8

把参数写入 `<vault>/书库/<book_dir>/.book-workflow.json` 作为本次 run 的配置档。

## Phase 1 — 环境检查 + vault 准备

```bash
python3 --version
which ebook-convert pandoc   # 线 A 才需要
python3 -m pip install -r {baseDir}/requirements.txt
```

vault 骨架（**仅 vault 不存在时建**，不要覆盖用户已有内容）：

```
<vault>/
├── CLAUDE.md            ← 用 templates/vault_CLAUDE.md
├── index.md             ← 用 templates/vault_index.md
├── 书库/
│   └── <book_dir>/
│       ├── CLAUDE.md    ← 用 templates/book_CLAUDE.md
│       ├── index.md     ← 用 templates/book_index.md
│       ├── 00_全本中译/
│       ├── 01_章节精读/
│       └── 02_主题笔记/
└── 主题/
```

> **重要**：vault 根**不要**自动建 `日记/`、`灵感/`、`项目/` 之类，除非用户明确要做综合性第二大脑。本 skill 默认 vault 是读书笔记专用。

## Phase 2 — 线 A 启动（后台）

如果用户选了线 A：

```bash
mkdir -p <vault>/书库/<book_dir>/00_全本中译/
cd <vault>/书库/<book_dir>/00_全本中译/
python3 {baseDir}/scripts/convert.py "<book_path>" --olang "<target_lang>"
```

之后按线 A 的 7 步流程（与原 translate-book 一致）：discover chunks → build glossary → parallel subagent translate → merge meta per batch → verify → translate title → merge_and_build。

线 A **可以后台跑**：`Bash run_in_background=true`。如果用户选了 A+B，先启动线 A 再进 Phase 3。

> 注：78+ chunks 时建议让 line A 跑独立长任务，不要在主对话里逐个 spawn subagent —— 会爆 context。可考虑：
> 1. 写一个独立 shell 脚本调用 claude CLI 顺序翻译，后台 nohup 起
> 2. 或单 dispatching agent 内部并行

具体术语表 / merge / build 细节见原 [translate-book SKILL.md](https://github.com/deusyu/translate-book/blob/main/SKILL.md)。

## Phase 3 — 线 B 提取章节结构

```bash
python3 {baseDir}/scripts/extract_book.py "<book_path>" \
    -o "<vault>/书库/<book_dir>/.extracted.json"
```

读 JSON 输出，做章节分组：

- **PDF**：优先用 PDF 自带 outline (`fitz.open(...).get_toc()`)。如果没 outline，再用 metadata + 目录页 fallback
- **EPUB/MOBI**：天然按章节
- **TXT**：按章节标记或固定行数

产出 `01_章节精读/00_章节地图.md`：

```markdown
# 章节地图 — <书名>

| # | 章节 | 英文标题 | 页 | 状态 | 链接 |
|---|------|---------|----|------|------|
| 0 | 引言 | Introduction | 1–12 | ⬜ | [[第00章_Introduction]] |
| 1 | ... | ... | ... | ⬜ | [[第01章_xxx]] |
```

**不再创建每章子目录**。章节笔记本身将在 Phase 4 直接作为平铺单文件创建，文件名格式 `第NN章_<英文 slug>.md`。

## Phase 4 — 线 B 章节循环

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

# 第 N 章 — 中英标题

## [具体物件/场景小标题 1]

[第一人称中文叙述]

> "short English quote from book"
> 中文对照（p.XX）

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

PDF 自带 outline 里有时**两个层级混在一起**——L1 是章节，L2 是子节；或者 L1 是 part 扉页（如 "ROBERT MOSES"、"INTERVIEWING"），L2 才是真正的章节。

**Caro 的 *Working* 是典型例子**：原书有 4 个 part 扉页（ROBERT MOSES / LYNDON JOHNSON / INTERVIEWING / THE PARIS REVIEW INTERVIEW）。它们**只有标题，没有正文**——是 part divider，不是章节。如果当章节处理，会产生 4 个 0KB 的"假章节"，挤占真章节的编号。

**正确做法**：

1. 用 `fitz.open(pdf).get_toc()` 拿 outline，区分 part vs chapter（通常 L1 + 后面紧跟 L2 的就是 part）
2. **Part 用平级文件**（不要文件夹——Obsidian 默认把文件夹聚到顶端）。文件名 `第N部_<slug>.md`，N = part 在书里的顺序（1, 2, 3, 4…）
3. 真章节用 `第NN章_<slug>.md`，NN = 章节号（两位数），连续不跳号
4. **所有文件加阅读顺序数字前缀 `NN_`**：从 `01_` 开始按阅读顺序递增。这是**最可靠的排序方式**——不依赖 Unicode 字典序的巧合。例如：
   - `04_第00章_引言.md`
   - `05_第01章_翻遍每一页.md`
   - `06_第1部_罗伯特·摩西.md`  ← part 扉页
   - `07_第02章_城市塑造者.md`
   - `08_第03章_碳足迹.md`
   - `09_第04章_作家的圣所.md`
   - `10_第2部_林登·约翰逊.md`
   - …
5. 前言/封皮等非章节内容用 `01_前言_xxx.md` 等格式，同样的递增前缀
6. **Part 扉页文件只放标题**（`# 罗伯特·摩西`），没有正文导航之类——导航全在 book root `index.md` 里。原书 part 扉页本来就空（只有大标题）
7. **Line A 和 Line B 镜像同一结构**：相同的 `NN_` 前缀、相同的 `第NN章` / `第N部` 编号，文件名中文 vs 英文
8. 章节间双链用 **完整 basename `[[NN_第XX章_xxx]]`** 或带显示名 `[[NN_第XX章_xxx|显示名]]`

### Book 目录入口 = book root index.md（不要在 00_全本中译/ 里再加 index）

每本书的入口是 **`书库/<book_dir>/index.md`**，不在 `00_全本中译/` 再起一个 index。这一个文件包含：

- 章节表（按 part 分组，每行：中文译本链接 + 精读笔记链接）
- 中文版下载（epub/pdf/docx 链接到 `00_全本中译/其他格式/`）
- 主题笔记链接（线 C 产物）
- 术语表链接
- 元信息

`01_章节精读/00_章节地图.md` 仍然保留——它是章节进度追踪表，可以在 book root index 里链过去。

### 写作风格规范（写每一章都必须遵守）

1. **第一人称**：用作者本人的"我"复述脉络，不要用"他"。这本书是第几人称就用第几人称；这本书什么语气就尽量贴什么语气。
2. **语言风格紧贴作者**：直白、具体、句中有物（名字、数字、地点、时间）。不抽象总结、不评判作者写得好不好。
3. **小标题**：2-3 字，**来自章节里具体物件/场景**（如"三明治"、"163 英里"、"乒乓球"、"无花果酱"）。**禁止**用"核心内容"、"主要论点"、"与全书主题的关联"、"要点清单"这类通用学术抬头。
4. **嵌入式精译**：关键原文短句以引用块嵌入（每章约 6-10 处），紧跟一行中文对照 + 页码。挑作者本人有强语气、强动作、强细节的瞬间。不要嵌大段（fair use + 可读性）。
5. **不写"为什么挑这段"前缀**。原文嵌入后直接接叙事，理由（如果非说不可）一句话融进上下文。
6. **编辑解读 section**：3-5 条，每条**描述书中内容**或**补充必要背景**——只在"读者不知道这点会读不懂某段"时才写。不要罗列"作者方法论 1/2/3/4"那种抽象总结。不要夸"高难度的招"、"修辞武器"。
7. **不写元说明**：不要写"以下是我以第一人称视角复述"、"以下是我以局外人身份的补充"、"留给你写"等元注释。
8. **`<!-- HUMAN -->` 块**留空给用户写，AI 改稿时绕过。
9. **章节地图状态**：完成后更新对应行 ⬜ → ✅。

### 循环节奏

```
for chapter in chapters:
    if status == "✅": continue
    if first_chapter or user_requested_pause:
        produce file
        pause: 风格 OK？批量推进？
    else:
        produce file (batch with 3-5 others)
        update map
```

第 1 章先停一次确认风格。之后每 3-5 章给一次小结。

## Phase 5 — 线 C 主题归纳

线 B 全部完成后，扫描所有章节精读文件的"编辑解读"和小标题，识别反复出现的主题，为每个主题产出一份笔记到 `02_主题笔记/`：

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

## Phase 6 — 线 A 完成后挂进 vault

线 A 完成后调用 `postprocess_book.py`，**一条命令完成所有后处理**：

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
├── index.md            ← 由 main agent 在 Phase 6 之后写
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

然后 main agent 写 `00_全本中译/index.md`（用 Obsidian 双链列出所有章节 + `其他格式/` 入口），并在 book_dir 的 `index.md` 顶部加链接。

如果线 A 失败：在 `00_全本中译/_FAILED.md` 写诊断信息。

## Phase 7 — 最终报告

向用户汇报：
- 线 A 产物路径 + 大小
- 线 B：N 章 ✅，Obsidian 路径，MOC 链接
- 线 C：M 篇主题笔记
- 下一步建议（在 Obsidian 读、批注、跨书互联）

## 断点续跑

每个 Phase 可中断重入：
- 参数存 `.book-workflow.json`
- 线 A 自带 chunk-level resume
- Phase 3 检查 `.extracted.json` 已存在
- Phase 4 检查章节地图状态字段
- 用户重新 `/book-workflow` 应提示"检测到未完成 run，继续？"

## 失败处理

| 问题 | 处理 |
|------|------|
| Calibre 缺失 | 提示装：`brew install --cask calibre`；线 A 跳过 |
| PDF 是扫描版（content_pages = 0） | 提示用户 OCR：`ocrmypdf --language chi_sim+eng in.pdf out.pdf` |
| 翻译 chunk 失败 | 自动重试 1 次，仍失败的写进 _FAILED.md |
| extract_book 失败 | 看是不是 MOBI（建议转 EPUB）或缺依赖 |
| vault 路径不存在 | 创建之，不要报错退出 |
| 用户清理后重跑 pandoc/ebook-convert 发现没图 | **教训**：`merge_and_build.py` 输出的 epub/pdf/docx **嵌了图**；如果用户事后让删 temp，必须**先把 `temp/images/` 挪到 `00_全本中译/images/`**，再清 temp。output.md 里图片是相对引用 `images/000NNN.jpg`——挪到平级目录后还能解析 |
| 重生成 epub/pdf 前要先备份带图老版 | 重跑 pandoc 会 overwrite 同名 epub/pdf/docx。如果需要清洗 output.md 后重生成，先 `cp book.epub book.epub.bak`，确认新版图正常再删 bak |

## 附录：翻译 Prompt（线 A subagent）

复用 [translate-book SKILL.md 第 156-218 行](https://github.com/deusyu/translate-book/blob/main/SKILL.md)。每个 subagent prompt 末尾注入 `print-terms-for-chunk` 输出的术语表。

**已知陷阱**：subagent 偶尔把**章节标题降级为普通段落**——原文如果一个章节用大字号或装饰排版（如首字下沉 + 全大写 + 居中），subagent 可能识别为段落而不是 `##` 标题。这造成 line A 切分时章节数少于实际章数。

**对策**：

1. **预防**：在翻译 prompt 里额外加一条——"如果原文里某行短文本（< 50 字）独占一段且后面紧跟章节内容，特别是与目录页（TOC）里的标题文字匹配的，必须输出为 `## 标题` 而不是普通段落"。
2. **检查**：`postprocess_book.py` 在切分前**对比 PDF outline**：
   - `python3 -c "import fitz; print(len(fitz.open('book.pdf').get_toc()))"` 拿真值章节数
   - 数 `output.md` 里的 `##` 数量
   - 如果差距 > 2，在 `00_全本中译/_HEADINGS_MISMATCH.md` 列出 outline 章节标题 + 各章在中文里可能的对应位置（用首句关键词搜索），让 main agent 或用户手工修复

## 附录：章节标题对齐脚本

`scripts/realign_headings.py`（待写）：读 PDF outline + 中文 output.md，把缺失的 `##` 标题手工/半自动加回去。流程：

```python
# 1. 用 fitz.open(pdf).get_toc() 拿到 (level, title, page) 列表
# 2. 对每个 outline title，在 output.md 里搜中文版本
#    - 简单：搜书名号《》或带冒号的：开头
#    - 进阶：调小 LLM 模糊匹配
# 3. 在匹配位置插入 `## 中文标题`
# 4. 删 TOC 区的重复标题
```
