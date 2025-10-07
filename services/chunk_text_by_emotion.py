# ──────────────────────────────────────────────────────────────
# <텍스트 → 감정 청크>
# find_turning_points_in_text() 로 얻은 ‘감정 전환점’ 리스트를 이용해
# 원본 txt 파일을 **감정 흐름‑단위 청크**로 다시 잘라 준다.
# ──────────────────────────────────────────────────────────────
import os
from typing import List, Tuple, Dict, Any
from utils.logger import log
from services.find_turning_points_in_text import find_turning_points_in_text


def chunk_text_by_emotion(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """메모리 효율적인 텍스트 청킹"""

    text_len = len(text)
    log(f"파일 길이: {text_len:,}자")
    
    # 매우 큰 텍스트의 경우 청크 수 제한
    if text_len > 50000:  # 5만자 이상
        log("큰 텍스트 감지: 처리 시간 최적화 모드")
        max_chunks = 15
    else:
        max_chunks = 30
    
    points = find_turning_points_in_text(text)
    if not points:
        return [(text, {"emotions": "unknown", "next_transition": None})]

    # 메모리 효율을 위해 청크별로 즉시 처리
    chunks = []
    last_position = 0
    
    for i, pt in enumerate(points[:max_chunks]):  # 청크 수 제한
        positon = pt.get("position_in_full_text", 0)
        if positon <= last_position:
            continue
            
        part = text[last_position:positon].strip()
        if part and len(part) > 10:  # 너무 짧은 청크 제외
            emotion_now = pt.get("emotions_before", "unknown") if i == 0 else points[i-1].get("emotions_after", "unknown")
            chunks.append((part, {
                "emotions": emotion_now,
                "next_transition": {
                    "to": pt.get("emotions_after", "unknown"),
                    "significance": pt.get("significance", 1),
                    "explanation": pt.get("explanation", "")
                }
            }))
        last_position = positon
    
    # 마지막 부분 처리
    final = text[last_position:].strip()
    if final and len(final) > 10:
        last_emotion = points[-1].get("emotions_after", "unknown") if points else "unknown"
        chunks.append((final, {"emotions": last_emotion, "next_transition": None}))

    log(f"청크 {len(chunks)}개 생성 (최대 {max_chunks}개 제한)")
    
    # 메모리 해제
    del text
    return chunks