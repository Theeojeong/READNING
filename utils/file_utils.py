# utils/file_utils.py
import os
import re
import unicodedata
from pathlib import Path

def save_text_to_file(path: str, text: str) -> None:
    # pathlib.Path 객체로 변환
    p = Path(path)
    # 부모 디렉터리 생성 (중첩 폴더까지 한 번에)
    p.parent.mkdir(parents=True, exist_ok=True)
    # 파일 쓰기
    p.write_text(text, encoding="utf-8")

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def delete_files_in_directory(path: str, extension: str = ".wav", exclude_files: list[str] = []):
    for filename in os.listdir(path):
        if filename.endswith(extension) and filename not in exclude_files:
            os.remove(os.path.join(path, filename))

def secure_filename(name: str) -> str:
    
    normalized = unicodedata.normalize("NFKD", name)
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
    name = unicodedata.normalize("NFC", "".join(transliterated))

    name = re.sub(r"[^\w.-]+", "_", name)

    name = name.strip("._")
    
    return name or "file"
