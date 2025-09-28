import nltk, os
from pprint import pprint
from config import MAX_SEGMENT_SIZE, OVERLAP_SIZE
from typing import Generator, Tuple
from nltk.tokenize import sent_tokenize
from utils.logger import log

NLTK_DIR = os.path.join(os.path.dirname(__file__), "..", "nltk_data")
nltk.data.path.append(NLTK_DIR)      # 프로젝트 안 캐시 경로 추가

def ensure_punkt() -> None:
    """punkt 토크나이저가 없으면 다운로드한다(최초 1회)."""
    try:
        nltk.data.find("tokenizers/punkt")
        print("NLTK 'punkt' 확인 완료.")
    except LookupError:
        print("NLTK 'punkt' 다운로드 중...")
        nltk.download("punkt", download_dir=NLTK_DIR, quiet=True)
        print("NLTK 'punkt' 다운로드 완료.")

ensure_punkt() 

def split_text_into_processing_segments(text: str) -> Generator[Tuple[str, int], None, None]:
    """
    원리(요약)
    
    1) 본문 텍스트에서 최대 길이(MAX_SEGMENT_SIZE)만큼 자릅니다. → 2600자 -> 3b 모델에게 안정적인 글자 수
    2) 잘린 지점이 ‘문장의 중간’인 경우 → search_text(마지막 20 % 구간)에서 뒤에서부터 완전한 문장 끝을 찾아 end 보정
    3) yield (청크본문, 원본에서 시작 위치)
    4) 다음 청크는 end‑OVERLAP_SIZE(겹침)부터 시작
    """
    n = len(text)                                   # 텍스트 전체 글자 수
    if n <= MAX_SEGMENT_SIZE:                       # 1. 전체 텍스트가 한 번에 들어가면 
        yield text, 0                               # 그대로 반환하고 종료
        return

    start = 0                                       # 청크 시작 위치
    while start < n:
        end = min(start + MAX_SEGMENT_SIZE, n)      # 2. 우선 최대 길이 지점까지 잘라 본다

        
        if end < n:                                 # 3. 만약 잘린 지점이 문장 중간이라면
            search_start = max(start + int(MAX_SEGMENT_SIZE * 0.8), start) # 3-1 마지막 20% 구간부터 끝(+200자 여유)만 검사
            search_text = text[search_start:min(end + 200, n)]
            try:
                sentences = sent_tokenize(search_text)
                if sentences:
                    best_end = end
                    for sentence in reversed(sentences): # 3-2 뒤에서부터 완전한 문장 끝을 찾아 end 보정
                        idx = search_text.rfind(sentence)
                        if idx != -1:
                            abs_end = search_start + idx + len(sentence)
                            if start < abs_end <= start + MAX_SEGMENT_SIZE:
                                best_end = abs_end
                                break
                    end = best_end
            except Exception as e:
                log(f"문장 토큰화 오류(무시): {e}")

        yield text[start:end], start # 가공이 끝난 청크를 호출자에게 전달
        if end == n:
            break
        start = max(start + 1, end - OVERLAP_SIZE) # 다음 청크 시작 위치 갱신
                                                   # (겹침 OVERLAP_SIZE 만큼 뒤로 물러서 맥락 유지)
    log("텍스트 분할 완료")