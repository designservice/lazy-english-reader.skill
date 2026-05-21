# 失败处理

| 问题 | 处理 |
|------|------|
| Calibre 缺失 | 提示装：`brew install --cask calibre`；全本翻译跳过 |
| PDF 是扫描版（content_pages = 0） | 提示用户 OCR：`ocrmypdf --language chi_sim+eng in.pdf out.pdf` |
| 翻译 chunk 失败 | 自动重试 1 次，仍失败的写进 _FAILED.md |
| extract_book 失败 | 看是不是 MOBI（建议转 EPUB）或缺依赖 |
| vault 路径不存在 | 创建之，不要报错退出 |
| 用户清理后重跑 pandoc/ebook-convert 发现没图 | **教训**：`merge_and_build.py` 输出的 epub/pdf/docx **嵌了图**；如果用户事后让删 temp，必须**先把 `temp/images/` 挪到 `00_全本中译/images/`**，再清 temp。output.md 里图片是相对引用 `images/000NNN.jpg`——挪到平级目录后还能解析 |
| 重生成 epub/pdf 前要先备份带图老版 | 重跑 pandoc 会 overwrite 同名 epub/pdf/docx。如果需要清洗 output.md 后重生成，先 `cp book.epub book.epub.bak`，确认新版图正常再删 bak |
