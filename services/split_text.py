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

# 문장 경계 탐색 관련 상수
SENTENCE_SEARCH_RATIO = 0.8  # 마지막 20% 구간만 검사
LOOKAHEAD_CHARS = 200        # 문장 끝을 찾기 위한 여유 문자 수


def _find_sentence_boundary(
    text: str,
    start_pos: int,
    initial_end_pos: int,
    max_end_pos: int
) -> int:
    # 검색 구간 설정: 마지막 20% 구간만 검사 (성능 최적화)
    search_start = max(
        start_pos + int(MAX_SEGMENT_SIZE * SENTENCE_SEARCH_RATIO),
        start_pos
    )
    search_end = min(initial_end_pos + LOOKAHEAD_CHARS, max_end_pos)
    search_text = text[search_start:search_end]
    
    try:
        sentences = sent_tokenize(search_text)
        if not sentences:
            return initial_end_pos
        
        # 뒤에서부터 완전한 문장 끝 찾기
        for sentence in reversed(sentences):
            sentence_pos = search_text.rfind(sentence)
            if sentence_pos == -1:
                continue
            
            # 절대 위치 계산
            absolute_end = search_start + sentence_pos + len(sentence)
            
            # 유효 범위 내에 있는지 확인
            if start_pos < absolute_end <= start_pos + MAX_SEGMENT_SIZE:
                return absolute_end
        
        return initial_end_pos
        
    except Exception as e:
        log(f"문장 토큰화 오류(무시): {e}")
        return initial_end_pos


def split_text_into_processing_segments(text: str) -> Generator[Tuple[str, int], None, None]:

    total_length = len(text)
    
    # 1단계: 짧은 텍스트는 분할 불필요
    if total_length <= MAX_SEGMENT_SIZE:
        yield text, 0
        return
    
    # 2단계: 텍스트를 순회하며 청크 생성
    current_pos = 0
    
    while current_pos < total_length:
        # 최대 크기만큼 자르기
        chunk_end = min(current_pos + MAX_SEGMENT_SIZE, total_length)
        
        # 텍스트가 더 남아있다면 문장 경계로 조정
        is_text_remaining = chunk_end < total_length
        if is_text_remaining:
            chunk_end = _find_sentence_boundary(
                text=text,
                start_pos=current_pos,
                initial_end_pos=chunk_end,
                max_end_pos=total_length
            )
        
        # 청크 반환
        chunk_text = text[current_pos:chunk_end]
        yield chunk_text, current_pos
        
        # 마지막 청크면 종료
        if chunk_end == total_length:
            break
        
        # 다음 청크 시작 위치 (맥락 유지를 위해 일부 겹침)
        next_pos = chunk_end - OVERLAP_SIZE
        current_pos = max(current_pos + 1, next_pos)
    
    log("텍스트 분할 완료")