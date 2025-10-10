import fitz
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import os
import re
from typing import List

from services.split_text import split_text_into_processing_segments

def extract_text_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(pages)

def detect_chapter_by_heading(text):
    """Detect chapters in ``text`` by common heading patterns.

    Consecutive duplicate headings are ignored. If the same heading appears
    again later in the document, a numeric suffix is appended so that each
    chapter title remains unique.
    """

    pattern = re.compile(
        r"(CHAPTER\s+\w+|Chapter\s+\d+|제\s*\d+\s*장|\d+\s*장)", re.MULTILINE
    )
    splits = pattern.split(text)

    if len(splits) < 3:
        return None  # Not reliable

    chapters = []
    title_counts: dict[str, int] = {}
    prev_title = None

    for i in range(1, len(splits), 2):
        raw_title = splits[i].strip()

        # Ignore repeated consecutive headings
        if raw_title == prev_title:
            continue
        prev_title = raw_title

        count = title_counts.get(raw_title, 0) + 1
        title_counts[raw_title] = count
        title = raw_title if count == 1 else f"{raw_title} ({count})"

        body = splits[i + 1].strip() if i + 1 < len(splits) else ""
        chapters.append({"title": title, "content": body})

    return chapters

def split_by_toc(text):
    # Look at first 3 pages to find likely ToC section
    toc_area = "\n".join(text.split("\n")[:200])
    candidates = re.findall(r"(?:(?:\d+\.\s+)?[A-Z][^\n]{5,100})", toc_area)
    candidates = [c.strip() for c in candidates if len(c.split()) > 2]

    if len(candidates) < 3:
        return None

    chapters = []
    for title in candidates:
        pattern = re.escape(title)
        match = re.search(pattern, text)
        if match:
            chapters.append((match.start(), title))
    
    chapters.sort()
    result = []
    for i in range(len(chapters)):
        start, title = chapters[i]
        end = chapters[i+1][0] if i+1 < len(chapters) else len(text)
        result.append({"title": title, "content": text[start:end].strip()})
    return result if len(result) >= 3 else None

def clean_pdf_text(raw_text):
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

def split_into_sentences(text):
    sentence_end = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    sentences = sentence_end.split(text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_by_sentences(text, n=300):
    clean_text = clean_pdf_text(text)
    sentences = split_into_sentences(clean_text)

    chunks = []
    for i in range(0, len(sentences), n):
        chunk_sentences = sentences[i:i+n]
        chunk = " ".join(chunk_sentences)
        chunks.append({"title": f"Chunk {i//n + 1}", "content": chunk})
    return chunks


def split_txt_into_pages(text_or_path: str) -> List[str]:

    if os.path.exists(text_or_path):
        with open(text_or_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = text_or_path

    pages: List[str] = []
    for seg, _ in split_text_into_processing_segments(text):
        pages.append(seg)
    return pages

def _deduplicate_chapter_titles(chapters: List[dict]) -> List[dict]:

    counts: dict[str, int] = {}
    for ch in chapters:
        base = ch.get("title", "")
        count = counts.get(base, 0)
        counts[base] = count + 1
        if count:
            ch["title"] = f"{base} ({count + 1})"
    return chapters


def split_pdf_into_chapters(pdf_path):
    text = extract_text_blocks(pdf_path)

    chapters = detect_chapter_by_heading(text)
    if chapters:
        print("Using chapter markers")
    else:
        print("Using fixed paragraph split")
        chapters = chunk_by_sentences(text)

    return _deduplicate_chapter_titles(chapters)


def split_epub_into_chapters(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            title = soup.title.string if soup.title else "Untitled"
            text = soup.get_text(separator="\n")
            chapters.append({'title': title.strip(), 'content': text.strip()})
    return chapters

def convert_and_split(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return split_pdf_into_chapters(file_path)
    elif ext == ".epub":
        return split_epub_into_chapters(file_path)
    else:
        raise ValueError("Unsupported file format. Only .pdf and .epub are supported.")