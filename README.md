# book-workflow

个人学习用的整书工作流 skill。两条线：

- **线 A**：把一本书（PDF/EPUB/MOBI/DOCX）全本翻译成目标语言，输出 epub/pdf/docx
- **线 B**：进 Obsidian 的逐章吸收型笔记（中英对照精译 + 章节综述 + 我的解读）
- **线 C**：全书读完后的主题归纳

## 触发

```
/book-workflow <path>
```

或自然语言："帮我读这本书 /path/to/book.pdf"。

## 依赖

```bash
# 线 A 必需
brew install --cask calibre
brew install pandoc

# Python 解析库
python3 -m pip install -r requirements.txt
```

## 产物位置

```
~/Documents/Obsidian/Vault/书库/<书名-作者>/
├── 00_全本中译/    ← 线 A
├── 01_章节笔记/    ← 线 B
└── 02_主题笔记/    ← 线 C
```

## 致谢

整合了以下开源项目的脚本和思路：

- [deusyu/translate-book](https://github.com/deusyu/translate-book) (MIT) — 并行 subagent 翻译流水线
- [hijiangtao/book-reader-skill](https://github.com/hijiangtao/book-reader-skill) — 多格式文本提取
- [alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) — Obsidian + Claude Code 方法论

License 文件分别在 `LICENSE-translate-book` 和 `LICENSE-book-reader`。
