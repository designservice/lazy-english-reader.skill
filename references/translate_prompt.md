# 全本翻译 worker prompt 与章节标题对齐

## 翻译 prompt（每个 worker 注入的模板）

复用 [translate-book SKILL.md 第 156-218 行](https://github.com/deusyu/translate-book/blob/main/SKILL.md)。每个 worker prompt 末尾注入 `print-terms-for-chunk` 输出的术语表。

**已知陷阱**：worker 偶尔把**章节标题降级为普通段落**——原文如果一个章节用大字号或装饰排版（如首字下沉 + 全大写 + 居中），worker 可能识别为段落而不是 `##` 标题。这造成全本翻译切分时章节数少于实际章数。

**根治方案（已实现，2026-05）**：`postprocess_book.py` 现在用 `.chapter_map.json` 作切分权威，**完全不依赖翻译后的 markdown 标题层级**。anchor-based 切分用工人 / 章节作者英文名（翻译保留）定位每章起点，绕过标题降级陷阱。

调用方式：

```bash
python3 postprocess_book.py <temp> <dest> \
    --title <书名> --author <作者> \
    --chapter-map <book_dir>/.chapter_map.json
```

详见 SKILL.md 的「核心原则：single source of truth」一节和 `scripts/postprocess_book.py` 里的 `split_by_chapter_map()` 实现。

**translate prompt 加固（仍然建议做，作为预防）**：在翻译 prompt 里额外加一条——"如果原文里某行短文本（< 50 字）独占一段且后面紧跟章节内容，特别是与目录页（TOC）里的标题文字匹配的，必须输出为 `## 标题` 而不是普通段落"。这是 belt-and-suspenders，**不是关键路径**——关键路径靠 `.chapter_map.json`。

**已弃用**：之前设想的 `scripts/realign_headings.py` 不再需要——chapter_map.json + anchor-based 切分把这件事解决了。
