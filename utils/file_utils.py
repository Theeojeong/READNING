# utils/file_utils.py
import os
import re
import unicodedata
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
    """파일에서 텍스트를 안전하게 로드 (인코딩 에러 처리)"""
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']
    
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except FileNotFoundError:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
        except Exception as e:
            raise Exception(f"파일 읽기 중 오류 발생: {e}")
    
    raise UnicodeDecodeError(f"지원되는 인코딩으로 파일을 읽을 수 없습니다: {path}")

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def delete_files_in_directory(path: str, extension: str = ".wav", exclude_files: list[str] = []):
    for filename in os.listdir(path):
        if filename.endswith(extension) and filename not in exclude_files:
            os.remove(os.path.join(path, filename))

def secure_filename(name: str) -> str:
    """Return a sanitized version of ``name`` safe for use as a filename.

    Unicode characters are preserved whenever possible.  Accented Latin
    characters are transliterated to their ASCII equivalents while other
    scripts remain unchanged.  Characters other than letters, numbers,
    ``.``, ``-`` or ``_`` are replaced with underscores.  If the resulting
    string is empty, ``"file"`` is returned.
    """

    # Normalize to NFKD to separate accent marks. Characters that can be
    # represented in ASCII are transliterated while others (e.g. Korean,
    # Chinese) are left as-is. This avoids dropping non-Latin characters
    # completely, unlike the traditional ``ascii``-only approach.
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

    # Replace characters outside of the safe set with underscores
    name = re.sub(r"[^\w.-]+", "_", name)

    # Trim leading/trailing periods/underscores and return a default if empty
    name = name.strip("._")
    return name or "file"
