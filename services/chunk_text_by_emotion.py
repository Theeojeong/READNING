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
    try:
        text = open(file_path, "r", encoding="utf-8").read()
    except Exception as e:
        log(f"파일 읽기 오류: {e}")
        return []

    log(f"파일 길이: {len(text)}자")
    points = find_turning_points_in_text(text)
    if not points:
        return [(text, {"emotions": "unknown", "next_transition": None})]

    chunks, last = [], 0
    for i, pt in enumerate(points):
        pos = pt["position_in_full_text"]
        part = text[last:pos].strip()
        if part:
            emotion_now = pt["emotions_before"] if i == 0 else points[i-1]["emotions_after"]
            chunks.append((part, {
                "emotions": emotion_now,
                "next_transition": {
                    "to": pt["emotions_after"],
                    "significance": pt["significance"],
                    "explanation": pt["explanation"]
                }
            }))
        last = pos
    # 마지막
    final = text[last:].strip()
    if final:
        chunks.append((final, {"emotions": points[-1]["emotions_after"], "next_transition": None}))

    log(f"청크 {len(chunks)}개 생성")
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