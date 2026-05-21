# 章节 vs 部分（重要区分）

> 在 Phase 4 处理 PDF outline 时读这一篇。

PDF 自带 outline 里有时**两个层级混在一起**——L1 是章节，L2 是子节；或者 L1 是 part 扉页（如 "ROBERT MOSES"、"INTERVIEWING"），L2 才是真正的章节。

**典型例子**：*War and Peace* 有 4 个 Volume + 1 Epilogue，每个 Volume 下面是 parts，parts 下面才是 chapters。Volume/Part 扉页**只有标题，没有正文**——它们是 dividers，不是章节。如果当章节处理，会产生若干 0KB 的"假章节"，挤占真章节的编号。许多自传体非虚构（按"Part I / Part II"组织成几大板块的）也是同样模式。

**正确做法**：

1. 用 `fitz.open(pdf).get_toc()` 拿 outline，区分 part vs chapter（通常 L1 + 后面紧跟 L2 的就是 part）
2. **Part 用平级文件**（不要文件夹——Obsidian 默认把文件夹聚到顶端）。文件名 `第N部_<slug>.md`，N = part 在书里的顺序（1, 2, 3, 4…）
3. 真章节用 `第NN章_<slug>.md`，NN = 章节号（两位数），连续不跳号
4. **所有文件加阅读顺序数字前缀 `NN_`**：从 `01_` 开始按阅读顺序递增。这是**最可靠的排序方式**——不依赖 Unicode 字典序的巧合。例如：
   - `04_第00章_前言.md`
   - `05_第01章_<章节标题>.md`
   - `06_第1部_<部标题>.md`  ← part 扉页
   - `07_第02章_<章节标题>.md`
   - `08_第03章_<章节标题>.md`
   - …
   - `10_第2部_<部标题>.md`
   - …
5. 前言/封皮等非章节内容用 `01_前言_xxx.md` 等格式，同样的递增前缀
6. **Part 扉页文件只放标题**（`# 部标题`），没有正文导航之类——导航全在 book root `index.md` 里。原书 part 扉页本来就空（只有大标题）
7. **全本翻译和章节精读镜像同一结构**：相同的 `NN_` 前缀、相同的 `第NN章` / `第N部` 编号，文件名中文 vs 英文
8. 章节间双链用 **完整 basename `[[NN_第XX章_xxx]]`** 或带显示名 `[[NN_第XX章_xxx|显示名]]`
