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
    # Pattern 1: Chapter markers
    pattern = re.compile(r"(CHAPTER\s+\w+|Chapter\s+\d+|제\s*\d+\s*장|\d+\s*장)", re.MULTILINE)
    splits = pattern.split(text)

    if len(splits) < 3:
        return None  # Not reliable
    chapters = []
    for i in range(1, len(splits), 2):
        title = splits[i].strip()
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
    """Split raw text into page-sized chunks similar to the frontend.

    This uses the same logic as ``split_text_into_processing_segments`` to
    ensure pages do not cut sentences abruptly. ``text_or_path`` may be either
    a string of text or a path to a ``.txt`` file.
    """

    if os.path.exists(text_or_path):
        with open(text_or_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = text_or_path

    pages: List[str] = []
    for seg, _ in split_text_into_processing_segments(text):
        pages.append(seg)
    return pages

def split_pdf_into_chapters(pdf_path):
    text = extract_text_blocks(pdf_path)

    chapters = detect_chapter_by_heading(text)
    if chapters:
        print("Using chapter markers")
        return chapters

    print("Using fixed paragraph split")
    return chunk_by_sentences(text)


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

# Example usage
# if __name__ == "__main__":
#     file_path = "Demian_교양_심리 소설.pdf"
#     chapters = convert_and_split(file_path)
#     for i, ch in enumerate(chapters):
#         print(f"--- {ch['title']} ---\n{ch['content'][:300]}...\n")