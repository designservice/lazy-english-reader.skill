# book-workflow.skill

**Claude Code skill**——把一本书变成 Obsidian 里的可阅读、可批注、可双链的知识结构。

> 注意：这是 [Claude Code](https://claude.ai/code) 的 skill（`/`-style command），不是独立软件。装在 `~/.claude/skills/book-workflow/` 即可被 Claude Code 自动识别。其他平台（Codex、Cursor 等）也能调用里面的 Python 脚本，但需要自己手工编排。

## 三条线（都可选）

| 线 | 做什么 | 何时跑 |
|---|---|---|
| **A · 全本翻译** | 用并行 subagent + Calibre/Pandoc 把外文书翻译成中文（或其他语言），输出 epub/pdf/docx | **可选**：只有你想要"整本中译"作为备查时才跑 |
| **B · 章节精读** | 进 Obsidian 的逐章吸收型笔记：用作者第一人称中文复述 + 嵌入式短引文 + 编辑解读 | 核心。**外文书或中文书都适用**——中文书时跳过翻译，直接做精读 |
| **C · 主题归纳** | 全书读完后扫所有章节精读，产出跨章节的主题笔记 | 线 B 完成后做 |

**典型用法组合**：

- 想读一本外文书 + 整本中译 → 跑 A + B + C
- 想读外文书但不需要全本翻译，只要精读笔记 → 跑 B + C
- 读中文书 → 跑 B + C（线 A 跳过，因为不需要翻译）
- 想做大批量翻译给以后查 → 只跑 A

## 触发

在 Claude Code 里：

```
/book-workflow <书的路径>
```

或自然语言："帮我读这本书 /path/to/book.pdf"。Skill 会用 `AskUserQuestion` 一次问完 8 个参数，包含**跑哪几条线**。

## 依赖

```bash
# 线 A 必需（不跑 A 可以跳过这两个）
brew install --cask calibre
brew install pandoc

# Python 解析库（线 B 和 C 必需）
python3 -m pip install -r requirements.txt
```

## 产物位置

跑完后产物在 Obsidian vault 里：

```
~/Documents/Obsidian/Vault/书库/<书名-作者>/
├── index.md            ← 书的总入口（所有章节、产物链接）
├── CLAUDE.md           ← 给 AI 看的本书上下文
├── 00_全本中译/        ← 线 A 产物（按章节切分 + 其他格式/含 epub/pdf/docx/封面图）
├── 01_章节精读/        ← 线 B 产物
└── 02_主题笔记/        ← 线 C 产物
```

book_dir 命名规范：`<原书主标题>-<作者姓>`（详见 SKILL.md）

## 个人偏好声明

这个 skill 的默认选择是**有意见的**，反映个人审美。你想用大概率要 fork 改造：

- **章节精读用作者本人的第一人称中文复述**——不是"他说"，是"我说"
- 章节小标题来自**章节内具体物件/场景**（"三明治"、"163 英里"、"无花果酱"），**禁止**"核心论点 / 与全书主题的关联"这种学术抬头
- 嵌入式精译——原文短句 + 中文对照 + 页码，每章 6-10 处
- `编辑解读` section（不是"我的解读"，因为是 AI 写的不是用户写的）
- 文件名：`NN_第NN章_xxx.md` / `NN_第N部_xxx.md`，`NN_` 是阅读顺序前缀
- Part 扉页是平级文件不是文件夹（适配 Obsidian 默认排序）

不喜欢就 fork。

## 跨平台（Codex 等）

Skill 三个组成部分的可移植性：

| 部分 | Codex / 其他平台 |
|------|-----------------|
| `scripts/*.py` | ✅ 直接命令行调用 |
| `templates/*.md` | ✅ 纯模板 |
| `SKILL.md` 编排逻辑 | ⚠️ 引用了 Claude Code 特有工具（`Agent`、`AskUserQuestion`、`TaskCreate`），需手工翻译成对应平台的等价物 |

## 致谢

整合了以下开源项目的脚本和思路：

- [deusyu/translate-book](https://github.com/deusyu/translate-book) (MIT) — 并行 subagent 翻译流水线
- [hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill) — 多格式文本提取
- [alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) — Obsidian + Claude Code 方法论

License 文件：本项目 MIT（见 `LICENSE`），上游 LICENSE 在 `LICENSE-translate-book` 和 `LICENSE-book-reader`。
