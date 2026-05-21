# Agent 能力映射

不同 agent 对工具的命名不一样。本 skill 在描述任务时用以下能力名，请映射到你这个平台的等价工具：

| Skill 中的能力名 | 含义 |
|---|---|
| `Read` / `Write` / `Edit` | 文件读 / 写 / 编辑 |
| `Bash` | shell / 终端命令执行 |
| `Glob` / `Grep` | 文件搜索 |
| `AskUserQuestion` | 在对话中向用户提问 |
| `Agent` | 后台任务、worker、并行处理；若平台没有 worker 系统，串行执行即可 |

**`{baseDir}`** 表示这个 skill 的安装目录。Claude Code 下通常是 `~/.claude/skills/lazy-english-reader/`；其他 agent 请替换成本地实际路径。

**用户笔记保护**：永远不要覆盖用户已经写过的 Obsidian 内容，除非 workflow 明确说"这一步是安全覆盖"。`<!-- HUMAN -->` ... `<!-- /HUMAN -->` 块在 AI 改稿时必须绕过。

`scripts/*.py` 都是可命令行直接调用的 Python 脚本。`templates/*.md` 是普通 Markdown 模板，可以直接读取或复制。
