import re
import os

def secure_filename(book_title: str) -> str:
    """파일 시스템에서 금지된 문자만 제거"""
    # Windows/Linux/Mac에서 금지된 문자: < > : " / \ | ? *
    book_title = re.sub(r'[<>:"/\\|?*]+', "_", book_title)
    # 공백도 언더스코어로
    book_title = book_title.replace(" ", "_")
    # 양 끝 정리
    book_title = book_title.strip("._")
    if not book_title:
        raise ValueError("책 제목이 비어있거나 유효하지 않습니다")
    return book_title

def ensure_dir(directory: str) -> None:
    """디렉토리가 존재하지 않으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
