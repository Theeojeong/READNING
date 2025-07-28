# ──────────────────────────────────────────────────────────────
# <텍스트 → 감정 청크>
# find_turning_points_in_text() 로 얻은 ‘감정 전환점’ 리스트를 이용해
# 원본 txt 파일을 **감정 흐름‑단위 청크**로 다시 잘라 준다.
# ──────────────────────────────────────────────────────────────
import os
from typing import List, Tuple, Dict, Any
from utils.logger import log
from services.find_turning_points_in_text import find_turning_points_in_text

def chunk_text_by_emotion(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """메모리 효율적인 텍스트 청킹"""
    from utils.file_utils import load_text_from_file
    
    try:
        # 개선된 파일 읽기 함수 사용 (인코딩 에러 처리)
        text = load_text_from_file(file_path)
    except Exception as e:
        log(f"파일 읽기 오류: {e}")
        return []

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
    last_pos = 0
    
    for i, pt in enumerate(points[:max_chunks]):  # 청크 수 제한
        pos = pt.get("position_in_full_text", 0)
        if pos <= last_pos:
            continue
            
        part = text[last_pos:pos].strip()
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
        last_pos = pos
    
    # 마지막 부분 처리
    final = text[last_pos:].strip()
    if final and len(final) > 10:
        last_emotion = points[-1].get("emotions_after", "unknown") if points else "unknown"
        chunks.append((final, {"emotions": last_emotion, "next_transition": None}))

    log(f"청크 {len(chunks)}개 생성 (최대 {max_chunks}개 제한)")
    
    # 메모리 해제
    del text
    return chunks




# # ── ① 기존: 파일 경로를 받아 처리 ───────────────────────────────
# def chunk_text_by_emotion(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
#     try:
#         text = open(file_path, "r", encoding="utf-8").read()
#     except Exception as e:
#         log(f"파일 읽기 오류: {e}")
#         return []
#     return _chunk_core(text)

# # ── ② 추가: “텍스트 문자열”을 바로 받아 처리 ──────────────────
# def chunk_text_by_emotion_from_text(text: str) -> List[Tuple[str, Dict[str, Any]]]:
#     """
#     FastAPI 라우터처럼 이미 메모리에 올라온 문자열을
#     감정-단위 청크로 잘라 [(chunk_text, ctx), …] 반환.
#     """
#     return _chunk_core(text)

# # ── ③ 공통 로직을 헬퍼 함수로 분리  ────────────────────────────
# def _chunk_core(text: str) -> List[Tuple[str, Dict[str, Any]]]:
#     log(f"텍스트 길이: {len(text)}자")
#     points = find_turning_points_in_text(text)
#     if not points:
#         return [(text, {"emotions": "unknown", "next_transition": None})]

#     chunks, last = [], 0
#     for i, pt in enumerate(points):
#         pos  = pt["position_in_full_text"]
#         part = text[last:pos].strip()
#         if part:
#             emotion_now = pt["emotions_before"] if i == 0 else points[i-1]["emotions_after"]
#             chunks.append((part, {
#                 "emotions": emotion_now,
#                 "next_transition": {
#                     "to": pt["emotions_after"],
#                     "significance": pt["significance"],
#                     "explanation": pt["explanation"]
#                 }
#             }))
#         last = pos

#     final = text[last:].strip()
#     if final:
#         chunks.append((final, {"emotions": points[-1]["emotions_after"], "next_transition": None}))
#     log(f"청크 {len(chunks)}개 생성")
#     return chunks

# ----------------------------------------------------------------------------------------