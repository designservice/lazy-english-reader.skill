#!/usr/bin/env python3
"""
Multi-format Book Extractor - Extract text from PDF, EPUB, MOBI, TXT books.

Outputs a JSON file with page/chapter-by-page text content, filtering out
non-content sections (TOC, index, copyright, blank pages, etc.).

Usage:
    python3 scripts/extract_book.py <book_path> [-o <output.json>] [--max-pages N]

Supported formats:
    - PDF  (.pdf)   - via PyMuPDF (fitz)
    - EPUB (.epub)  - via ebooklib + BeautifulSoup
    - MOBI (.mobi)  - via mobi lib (converts internally)
    - TXT  (.txt)   - plain text, split by chapters or fixed-size chunks

Dependencies (install as needed):
    pip install pymupdf pypdf ebooklib mobi beautifulsoup4
"""

import sys
import json
import argparse
import re
import os
import shutil
from pathlib import Path


# --- Shared utilities ---

SKIP_PATTERNS = [
    r'(?i)^table\s+of\s+contents\s*$',
    r'(?i)^contents\s*$',
    r'^\u76ee\s*\u5f55\s*$',
    r'(?:\.\s*\.){5,}',
    r'(?i)all\s+rights?\s+reserved',
    r'(?i)ISBN[\s:\-]*[\dX\-]+',
    r'(?i)copyright\s*\xa9',
    r'\u7248\u6743\u6240\u6709',
    r'(?i)^bibliography\s*$',
    r'(?i)^references\s*$',
    r'^\u53c2\u8003\u6587\u732e\s*$',
    r'(?i)^acknowledgm?ents?\s*$',
    r'^\u81f4\u8c22\s*$',
]

MIN_TEXT_LENGTH = 80


def _pip_install_hint(*pkgs):
    quoted = " ".join(pkgs)
    return "%s -m pip install %s" % (sys.executable or "python3", quoted)


def _missing_dependency_error(module_name, install_hint):
    return ModuleNotFoundError("Missing dependency: %s. Install with: %s" % (module_name, install_hint))


def is_skip_content(text):
    stripped = text.strip()
    if len(stripped) < MIN_TEXT_LENGTH:
        return True
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, stripped, re.MULTILINE):
            return True
    lines = [l.strip() for l in stripped.split('\n') if l.strip()]
    if lines:
        short_lines = sum(1 for l in lines if len(l) < 5)
        if len(lines) > 10 and short_lines / len(lines) > 0.6:
            return True
    toc_hits = re.findall(r'\.{2,}\s*\d+', stripped)
    if len(toc_hits) > 5:
        return True
    return False


def extract_html_title(html_content):
    for pattern in (
        r'<h1[^>]*>(.*?)</h1>',
        r'<h2[^>]*>(.*?)</h2>',
        r'<h3[^>]*>(.*?)</h3>',
        r'<title[^>]*>(.*?)</title>',
    ):
        m = re.search(pattern, html_content, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            continue
        raw = re.sub(r'<[^>]+>', ' ', m.group(1))
        raw = raw.replace('\xa0', ' ')
        raw = re.sub(r'\s+', ' ', raw).strip()
        if raw:
            return raw[:200]
    return None


def html_to_text(html_content):
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError:
        from html.parser import HTMLParser

        class _TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self._parts = []
                self._skip_depth = 0
                self._skip_tags = {"script", "style", "nav", "header", "footer"}

            def handle_starttag(self, tag, attrs):
                tag = (tag or "").lower()
                if tag in self._skip_tags:
                    self._skip_depth += 1

            def handle_endtag(self, tag):
                tag = (tag or "").lower()
                if tag in self._skip_tags and self._skip_depth > 0:
                    self._skip_depth -= 1
                if self._skip_depth == 0 and tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5"}:
                    self._parts.append("\n")

            def handle_data(self, data):
                if self._skip_depth > 0:
                    return
                if data:
                    self._parts.append(data)

        parser = _TextExtractor()
        parser.feed(html_content or "")
        text = "".join(parser._parts)
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(line for line in lines if line)

    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


# --- PDF extractor ---

def extract_pdf(file_path, max_pages=0):
    try:
        import fitz
    except ModuleNotFoundError:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as e:
            raise _missing_dependency_error("pymupdf/fitz or pypdf", _pip_install_hint("pymupdf", "pypdf")) from e

        reader = PdfReader(str(file_path))
        total_pages = len(reader.pages)
        limit = min(max_pages, total_pages) if max_pages > 0 else total_pages

        result = {
            "metadata": {
                "filename": Path(file_path).name,
                "format": "pdf",
                "total_pages": total_pages,
                "processed_pages": 0,
                "content_pages": 0,
                "skipped_pages": 0,
            },
            "pages": []
        }

        for i in range(limit):
            page = reader.pages[i]
            text = page.extract_text() or ""
            if is_skip_content(text):
                result["metadata"]["skipped_pages"] += 1
                continue
            result["pages"].append({
                "page_number": i + 1,
                "title": "Page %d" % (i + 1),
                "text": text.strip()
            })
            result["metadata"]["content_pages"] += 1

        result["metadata"]["processed_pages"] = limit
        return result

    doc = fitz.open(str(file_path))
    total_pages = doc.page_count
    limit = min(max_pages, total_pages) if max_pages > 0 else total_pages

    result = {
        "metadata": {
            "filename": Path(file_path).name,
            "format": "pdf",
            "total_pages": total_pages,
            "processed_pages": 0,
            "content_pages": 0,
            "skipped_pages": 0,
        },
        "pages": []
    }

    for i in range(limit):
        text = doc[i].get_text("text")
        if is_skip_content(text):
            result["metadata"]["skipped_pages"] += 1
            continue
        result["pages"].append({
            "page_number": i + 1,
            "title": "Page %d" % (i + 1),
            "text": text.strip()
        })
        result["metadata"]["content_pages"] += 1

    result["metadata"]["processed_pages"] = limit
    doc.close()
    return result


# --- EPUB extractor ---

def extract_epub(file_path, max_pages=0):
    try:
        import ebooklib
        from ebooklib import epub
    except ModuleNotFoundError:
        import zipfile

        with zipfile.ZipFile(str(file_path)) as z:
            names = [
                n for n in z.namelist()
                if n.lower().endswith((".html", ".htm", ".xhtml"))
            ]
            names.sort()

            book_title = "Unknown"
            opf_candidates = [n for n in z.namelist() if n.lower().endswith(".opf")]
            if opf_candidates:
                try:
                    opf = z.read(opf_candidates[0]).decode("utf-8", errors="ignore")
                    m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", opf, flags=re.IGNORECASE | re.DOTALL)
                    if m:
                        book_title = re.sub(r"<[^>]+>", " ", m.group(1))
                        book_title = re.sub(r"\s+", " ", book_title).strip() or book_title
                except Exception:
                    pass

            total = len(names)
            limit = min(max_pages, total) if max_pages > 0 else total

            result = {
                "metadata": {
                    "filename": Path(file_path).name,
                    "format": "epub",
                    "book_title": book_title,
                    "total_pages": total,
                    "processed_pages": 0,
                    "content_pages": 0,
                    "skipped_pages": 0,
                },
                "pages": []
            }

            for idx, name in enumerate(names[:limit]):
                html_content = z.read(name).decode("utf-8", errors="ignore")
                text = html_to_text(html_content)
                if is_skip_content(text):
                    result["metadata"]["skipped_pages"] += 1
                    continue
                chapter_title = extract_html_title(html_content) or Path(name).stem
                result["pages"].append({
                    "page_number": idx + 1,
                    "title": chapter_title or ("Chapter %d" % (idx + 1)),
                    "text": text.strip()
                })
                result["metadata"]["content_pages"] += 1

            result["metadata"]["processed_pages"] = limit
            return result

    book = epub.read_epub(str(file_path), options={'ignore_ncx': True})

    book_title = "Unknown"
    try:
        t = book.get_metadata('DC', 'title')
        if t:
            book_title = t[0][0]
    except Exception:
        pass

    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    total = len(items)
    limit = min(max_pages, total) if max_pages > 0 else total

    result = {
        "metadata": {
            "filename": Path(file_path).name,
            "format": "epub",
            "book_title": book_title,
            "total_pages": total,
            "processed_pages": 0,
            "content_pages": 0,
            "skipped_pages": 0,
        },
        "pages": []
    }

    for idx, item in enumerate(items[:limit]):
        html_content = item.get_content().decode('utf-8', errors='ignore')
        text = html_to_text(html_content)

        if is_skip_content(text):
            result["metadata"]["skipped_pages"] += 1
            continue

        chapter_title = extract_html_title(html_content)

        result["pages"].append({
            "page_number": idx + 1,
            "title": chapter_title or ("Chapter %d" % (idx + 1)),
            "text": text.strip()
        })
        result["metadata"]["content_pages"] += 1

    result["metadata"]["processed_pages"] = limit
    return result


# --- MOBI extractor ---

def extract_mobi(file_path, max_pages=0):
    try:
        import mobi
    except ModuleNotFoundError as e:
        raise _missing_dependency_error(
            "mobi",
            _pip_install_hint("mobi") + " (or convert .mobi to .epub with calibre/ebook-convert)"
        ) from e

    tempdir, filepath = mobi.extract(str(file_path))
    try:
        extracted = Path(filepath)
        if extracted.suffix.lower() == '.epub':
            result = extract_epub(str(extracted), max_pages)
            result["metadata"]["format"] = "mobi"
            result["metadata"]["filename"] = Path(file_path).name
            return result
        elif extracted.suffix.lower() in ('.html', '.htm'):
            with open(extracted, 'r', encoding='utf-8', errors='ignore') as f:
                html = f.read()
            text = html_to_text(html)
            result = split_text_into_pages(text, Path(file_path).name, max_pages, "mobi")
            return result
        else:
            with open(extracted, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return split_text_into_pages(text, Path(file_path).name, max_pages, "mobi")
    finally:
        if tempdir and os.path.exists(tempdir):
            shutil.rmtree(tempdir, ignore_errors=True)


# --- TXT extractor ---

def extract_txt(file_path, max_pages=0):
    file_path = Path(file_path)
    text = None
    for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                text = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if text is None:
        raise ValueError("Cannot decode file: %s" % file_path)
    return split_text_into_pages(text, file_path.name, max_pages, "txt")


# --- Shared text splitter ---

CHAPTER_PATTERNS = [
    r'^#{1,3}\s+.+$',
    r'^(?:Chapter|CHAPTER)\s+\d+',
    r'^\u7b2c[\u4e00-\u9fa5\d]+[\u7ae0\u8282\u56de\u5377\u96c6\u7bc7]',
    r'^Part\s+\d+',
    r'^BOOK\s+\d+',
    r'^\*{3,}$',
    r'^-{3,}$',
]


def split_text_into_pages(text, filename, max_pages=0, fmt="txt"):
    """Split a large text into chapter-based or fixed-size chunks."""

    combined = '|'.join('(%s)' % p for p in CHAPTER_PATTERNS)

    chunks = []
    splits = re.split('(%s)' % combined, text, flags=re.MULTILINE)

    current_chunk = ""
    current_title = None

    for part in splits:
        if part is None:
            continue
        # Check if this part matches any chapter heading
        is_heading = False
        for p in CHAPTER_PATTERNS:
            if re.match(p, part.strip(), re.MULTILINE):
                is_heading = True
                break

        if is_heading:
            if current_chunk.strip():
                chunks.append((current_title, current_chunk.strip()))
            current_title = part.strip()[:80]
            current_chunk = part
        else:
            current_chunk += part

    if current_chunk.strip():
        chunks.append((current_title, current_chunk.strip()))

    # If no chapter markers or only 1 chunk, split by line count
    if len(chunks) <= 1:
        lines = text.split('\n')
        CHUNK_SIZE = 60
        chunks = []
        for i in range(0, len(lines), CHUNK_SIZE):
            chunk_lines = lines[i:i + CHUNK_SIZE]
            chunk_text = '\n'.join(chunk_lines)
            title = "Section %d" % (i // CHUNK_SIZE + 1)
            for line in chunk_lines[:5]:
                s = line.strip()
                if s and len(s) < 80 and not s.endswith(('.', ',', ';')):
                    title = s
                    break
            chunks.append((title, chunk_text))

    total = len(chunks)
    limit = min(max_pages, total) if max_pages > 0 else total

    result = {
        "metadata": {
            "filename": filename,
            "format": fmt,
            "total_pages": total,
            "processed_pages": 0,
            "content_pages": 0,
            "skipped_pages": 0,
        },
        "pages": []
    }

    for idx, (title, chunk_text) in enumerate(chunks[:limit]):
        if is_skip_content(chunk_text):
            result["metadata"]["skipped_pages"] += 1
            continue
        result["pages"].append({
            "page_number": idx + 1,
            "title": title or ("Section %d" % (idx + 1)),
            "text": chunk_text.strip()
        })
        result["metadata"]["content_pages"] += 1

    result["metadata"]["processed_pages"] = limit
    return result


# --- Main dispatcher ---

FORMAT_HANDLERS = {
    '.pdf': extract_pdf,
    '.epub': extract_epub,
    '.mobi': extract_mobi,
    '.txt': extract_txt,
    '.text': extract_txt,
    '.md': extract_txt,
    '.markdown': extract_txt,
}


def extract_book(file_path, max_pages=0):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError("File not found: %s" % file_path)
    ext = file_path.suffix.lower()
    handler = FORMAT_HANDLERS.get(ext)
    if handler is None:
        supported = ', '.join(sorted(FORMAT_HANDLERS.keys()))
        raise ValueError("Unsupported format: %s. Supported: %s" % (ext, supported))
    return handler(str(file_path), max_pages)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from books (PDF, EPUB, MOBI, TXT)")
    parser.add_argument("book_path", help="Path to the book file")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Max pages/chapters to process (0 = all)")
    args = parser.parse_args()

    book_path = Path(args.book_path)
    output_path = args.output or str(book_path.with_suffix('.json'))
    ext = book_path.suffix.lower()

    print("Extracting text from: %s (format: %s)" % (book_path.name, ext))
    result = extract_book(str(book_path), args.max_pages)

    meta = result["metadata"]
    unit = "chapters" if ext in ('.epub', '.mobi') else "pages/sections"
    print("Total %s: %d" % (unit, meta['total_pages']))
    print("Processed: %d" % meta['processed_pages'])
    print("Content: %d" % meta['content_pages'])
    print("Skipped: %d" % meta['skipped_pages'])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Output saved to: %s" % output_path)
    if result["pages"]:
        first = result["pages"][0]
        preview = first["text"][:200].replace('\n', ' ')
        print("First content (%s): %s..." % (first['title'], preview))


if __name__ == "__main__":
    main()
