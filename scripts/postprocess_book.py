#!/usr/bin/env python3
"""
后处理 line A 产物。

输入：translate-book 的 merge_and_build.py 产物（output.md, book.epub, book.pdf, book.docx）
+ temp dir 里的 images/

输出：按 `00_全本中译/` 的最终布局：
  - 根目录平铺每章 markdown（按 `##` 切分 output.md）
  - 子目录 `其他格式/`：用中文书名命名的 epub/pdf/docx/md + book-style.css + images/
  - 章节里的伪方括号清洗

用法：
  python3 postprocess_book.py <temp_dir> <vault_book_dir> \
      --title "工作的方法" --author "罗伯特·A·卡罗"
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CSS_TEMPLATE = SKILL_DIR / "templates" / "book-style.css"


def strip_pseudo_brackets(text):
    """去掉非链接的 `[文本]`（Calibre HTMLZ 转 markdown 时的伪影），保留真链接 `[text](url)` 和图片 `![alt](url)`。"""
    pattern = re.compile(r'(?<!\!)\[([^\[\]\n]*?)\](?!\()')
    prev = None
    out = text
    for _ in range(5):
        prev = out
        out = pattern.sub(r'\1', out)
        if out == prev:
            break
    return out


def clean_dropcaps(text):
    """清理 PDF 首字下沉残留：段首孤立大写字母、被【【【】】】或引号包裹的首字符。"""
    # 1. 段落开头孤立大写字母 + 空格 + 中文（W 在我研究... → 在我研究...）
    text = re.sub(r'(^|\n\n)([A-Z]) (?=[一-鿿])', r'\1', text)
    # 2. 【【【字】】】 → 字
    text = re.sub(r'【{2,}([一-鿿])】{2,}', r'\1', text)
    # 3. 段首被引号包的单字母
    text = re.sub(r'(^|\n\n)["\']([A-Z])["\']?\s+(?=[一-鿿])', r'\1', text)
    return text


def slugify(s):
    s = re.sub(r'[^\w一-鿿\-]', '_', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s[:40]


def split_by_chapters(output_md_path, root_dir):
    """按 `##` 标题把 output.md 切成多个章节文件，放到 root_dir。"""
    text = output_md_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    chapters = []
    current_title = "前言"
    current_lines = []
    chap_num = 0
    for line in lines:
        m = re.match(r'^##\s+(.+)$', line)
        if m:
            if current_lines:
                chapters.append((chap_num, current_title, '\n'.join(current_lines).strip()))
                chap_num += 1
            current_title = m.group(1).strip().strip('[]').strip('*').strip()
            current_lines = [f"# {current_title}", ""]
        else:
            current_lines.append(line)
    if current_lines:
        chapters.append((chap_num, current_title, '\n'.join(current_lines).strip()))

    for num, title, content in chapters:
        fname = f"{num:02d}_{slugify(title)}.md"
        (root_dir / fname).write_text(content + '\n', encoding='utf-8')

    return chapters


def find_cover(images_dir):
    """挑封面：first portrait-aspect-ratio JPG over 1000px tall."""
    try:
        from PIL import Image
    except ImportError:
        # 退化：第一张 JPG
        files = sorted(images_dir.glob('*.jpg'))
        return files[0] if files else None
    candidates = []
    for f in sorted(images_dir.glob('*.jpg')):
        try:
            im = Image.open(f)
            w, h = im.size
            if h > w and h > 1000:
                candidates.append((h, f))
        except Exception:
            pass
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    # fallback
    files = sorted(images_dir.glob('*.jpg'))
    return files[0] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("temp_dir", help="translate-book temp dir, contains output.md / book.* / images/")
    ap.add_argument("dest_dir", help="00_全本中译/ in vault")
    ap.add_argument("--title", required=True, help='Chinese book title, e.g. "工作的方法"')
    ap.add_argument("--author", required=True, help="Author")
    ap.add_argument("--keep-temp", action="store_true", help="don't delete temp dir after processing")
    args = ap.parse_args()

    temp = Path(args.temp_dir).resolve()
    dest = Path(args.dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    其他 = dest / "其他格式"
    其他.mkdir(exist_ok=True)

    title = args.title.strip().strip('《》')
    author = args.author.strip()

    # 1. 复制 + 清洗 output.md
    src_md = temp / "output.md"
    if not src_md.exists():
        print(f"ERROR: {src_md} not found. Did you run merge_and_build.py first?", file=sys.stderr)
        sys.exit(1)
    text = src_md.read_text(encoding='utf-8')
    print(f"output.md: {len(text)} chars, brackets before: {text.count('[') + text.count(']')}")
    cleaned = strip_pseudo_brackets(text)
    print(f"  brackets after: {cleaned.count('[') + cleaned.count(']')}")
    cleaned = clean_dropcaps(cleaned)
    print(f"  drop-cap artifacts cleaned")

    main_md = 其他 / f"{title}.md"
    main_md.write_text(cleaned, encoding='utf-8')

    # 2. 按 ## 切章节，写到 dest 根
    chapters = split_by_chapters(main_md, dest)
    print(f"split into {len(chapters)} chapter files")

    # 3. 清洗每个章节文件的伪方括号 + 首字下沉残留
    for f in sorted(dest.glob("*.md")):
        if f.parent != dest or f.name == 'index.md': continue
        t = f.read_text(encoding='utf-8')
        t = strip_pseudo_brackets(t)
        t = clean_dropcaps(t)
        f.write_text(t, encoding='utf-8')

    # 4. 挪 images
    src_imgs = temp / "images"
    dst_imgs = 其他 / "images"
    if src_imgs.exists():
        if dst_imgs.exists():
            shutil.rmtree(dst_imgs)
        shutil.copytree(src_imgs, dst_imgs)
        print(f"copied images: {len(list(dst_imgs.glob('*')))} files")

    # 5. 复制 glossary.json
    src_glo = temp / "glossary.json"
    if src_glo.exists():
        shutil.copy(src_glo, dest / "glossary.json")

    # 6. 复制 CSS 模板
    shutil.copy(CSS_TEMPLATE, 其他 / "book-style.css")

    # 7. 用 pandoc 重生成带封面、带 CSS 的 epub
    cover = find_cover(dst_imgs) if dst_imgs.exists() else None
    epub_path = 其他 / f"{title}.epub"
    cmd = [
        "pandoc", str(main_md), "-o", str(epub_path),
        "--css", str(其他 / "book-style.css"),
        "--metadata", f"title={title}",
        "--metadata", f"author={author}",
        "--metadata", "lang=zh-CN",
        "--toc", "--toc-depth=2",
    ]
    if cover:
        cmd += ["--epub-cover-image", str(cover.relative_to(其他))]
    print(f"running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=其他, check=False)

    # 8. epub → PDF（A5 + 页码 + 目录 + 章节换页）
    pdf_path = 其他 / f"{title}.pdf"
    subprocess.run([
        "ebook-convert", str(epub_path), str(pdf_path),
        "--pdf-page-numbers",
        "--pdf-default-font-size=14",
        "--paper-size=a5",
        "--pdf-add-toc",
        "--chapter=//*[name()='h1' or name()='h2']",
        "--extra-css", str(其他 / "book-style.css"),
    ], check=False)

    # 9. docx
    docx_path = 其他 / f"{title}.docx"
    subprocess.run([
        "pandoc", str(main_md), "-o", str(docx_path),
        "--metadata", f"title={title}",
        "--metadata", f"author={author}",
        "--toc",
    ], check=False)

    # 10. 清 temp
    if not args.keep_temp:
        shutil.rmtree(temp)
        print(f"deleted {temp}")

    print(f"\n=== done ===")
    print(f"dest: {dest}")
    for f in sorted(dest.glob("*.md")):
        print(f"  {f.name}")
    print(f"  其他格式/:")
    for f in sorted(其他.glob("*")):
        print(f"    {f.name}")


if __name__ == '__main__':
    main()
