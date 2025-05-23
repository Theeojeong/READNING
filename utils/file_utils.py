# utils/file_utils.py
import os
import re, unicodedata
from pathlib import Path

def save_text_to_file(path: str, text: str) -> None:
    """
    지정한 경로(폴더가 없으면 자동 생성)에 텍스트를 저장한다.
    """
    # 1️⃣ pathlib.Path 객체로 변환
    p = Path(path)
    # 2️⃣ 부모 디렉터리 생성 (중첩 폴더까지 한 번에)
    p.parent.mkdir(parents=True, exist_ok=True)
    # 3️⃣ 파일 쓰기
    p.write_text(text, encoding="utf-8")


def load_text_from_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def delete_files_in_directory(path: str, extension: str = ".wav", exclude_files: list[str] = []):
    for filename in os.listdir(path):
        if filename.endswith(extension) and filename not in exclude_files:
            os.remove(os.path.join(path, filename))

def secure_filename(name: str) -> str:
    """Safely normalizes a string for use as a filename.

    Unicode characters are decomposed using ``NFKD`` and any combining
    marks are removed so that accented Latin characters are transliterated
    to their ASCII base forms.  Remaining characters are retained and any
    that are not letters, numbers, ``.``, ``-`` or ``_`` are replaced with
    underscores.  The function falls back to ``"file"`` if the result is
    empty.
    """

    # Normalize and strip combining accents/marks
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    # Replace characters outside of the safe set with underscores
    name = re.sub(r"[^\w.-]+", "_", name)

    # Trim leading/trailing periods/underscores and return a default if empty
    name = name.strip("._")
    return name or "file"
