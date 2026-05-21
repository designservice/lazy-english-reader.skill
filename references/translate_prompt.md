# 全本翻译 worker prompt 与章节标题对齐

## 翻译 prompt（每个 worker 注入的模板）

复用 [translate-book SKILL.md 第 156-218 行](https://github.com/deusyu/translate-book/blob/main/SKILL.md)。每个 worker prompt 末尾注入 `print-terms-for-chunk` 输出的术语表。

**已知陷阱**：worker 偶尔把**章节标题降级为普通段落**——原文如果一个章节用大字号或装饰排版（如首字下沉 + 全大写 + 居中），worker 可能识别为段落而不是 `##` 标题。这造成全本翻译切分时章节数少于实际章数。

**对策**：

1. **预防**：在翻译 prompt 里额外加一条——"如果原文里某行短文本（< 50 字）独占一段且后面紧跟章节内容，特别是与目录页（TOC）里的标题文字匹配的，必须输出为 `## 标题` 而不是普通段落"。
2. **检查**：`postprocess_book.py` 在切分前**对比 PDF outline**：
   - `python3 -c "import fitz; print(len(fitz.open('book.pdf').get_toc()))"` 拿真值章节数
   - 数 `output.md` 里的 `##` 数量
   - 如果差距 > 2，在 `00_全本中译/_HEADINGS_MISMATCH.md` 列出 outline 章节标题 + 各章在中文里可能的对应位置（用首句关键词搜索），让协调 agent 或用户手工修复

## 章节标题对齐脚本

`scripts/realign_headings.py`（待写）：读 PDF outline + 中文 output.md，把缺失的 `##` 标题手工/半自动加回去。流程：

```python
# 1. 用 fitz.open(pdf).get_toc() 拿到 (level, title, page) 列表
# 2. 对每个 outline title，在 output.md 里搜中文版本
#    - 简单：搜书名号《》或带冒号的：开头
#    - 进阶：调小 LLM 模糊匹配
# 3. 在匹配位置插入 `## 中文标题`
# 4. 删 TOC 区的重复标题
```
