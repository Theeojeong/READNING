# utils/file_utils.py
import os
import re
import unicodedata
from pathlib import Path


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def secure_filename(book_title: str) -> str:
    
    normalized = unicodedata.normalize("NFKD", book_title)
    transliterated = []
    for ch in normalized:
        if unicodedata.combining(ch):
            continue
        try:
            ascii_char = ch.encode("ascii").decode("ascii")
        except UnicodeEncodeError:
            transliterated.append(ch)
        else:
            transliterated.append(ascii_char)
    book_title = unicodedata.normalize("NFC", "".join(transliterated))

    book_title = re.sub(r"[^\w.-]+", "_", book_title)

    book_title = book_title.strip("._")
    
    return book_title or "file"
