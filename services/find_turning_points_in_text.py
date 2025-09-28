# ──────────────────────────────────────────────────────────────
# <전환점 탐색>
# 전체 텍스트를 청크 제너레이터로 순회하면서
#  ▶ 각 청크에서 받은 emotional_phases 를 '원본 위치' 좌표로 환산
#  ▶ 너무 가까운 전환점(300자 미만)은 하나만 남기고 필터링
#  ▶ 최종 확정 전환점 리스트 반환
# ──────────────────────────────────────────────────────────────
from typing import List, Dict, Any
from utils.logger import log
from services.split_text import split_text_into_processing_segments
from services.analyze_emotions_with_gpt import analyze_emotions_with_gpt
from config import PRINT_CHUNK_TEXT, CHUNK_PREVIEW_LENGTH

def find_turning_points_in_text(text: str) -> List[Dict[str, Any]]:
    points      = []                # 모든 전환점 임시 저장
    last_position    = -float("inf")     # 직전 확정 전환점 위치
    segment_idx     = 0                 # 청크 번호 카운터

    for segment, segment_start in split_text_into_processing_segments(text):
        segment_idx += 1
        log(f"청크 {segment_idx}: 길이 {len(segment)}, 시작 {segment_start}")
        if PRINT_CHUNK_TEXT:
            preview = segment[:CHUNK_PREVIEW_LENGTH].replace('\n', ' ')
            log(f"청크 {segment_idx} 미리보기: {preview}…")

        analysis = analyze_emotions_with_gpt(segment)
        for p in analysis.get("emotional_phases", []):
            # 위치 계산
            snippet = p.get("start_text", "")[:100]
            rel = segment.find(snippet) if snippet else 0
            p["position_in_full_text"] = segment_start + rel
            points.append(p)

    # 위치 기반 정렬 및 최소 간격 필터
    points.sort(key=lambda x: x.get("position_in_full_text", 0))
    filtered = []
    min_gap = max(300, len(text) // 100)  # 텍스트 길이에 비례한 최소 간격
    max_points = 20  # 최대 전환점 수 제한
    
    for p in points:
        pos = p.get("position_in_full_text", 0)
        if pos - last_position >= min_gap and len(filtered) < max_points:
            filtered.append(p)
            last_position = pos
        elif len(filtered) >= max_points:
            break  # 무한 루프 방지
    
    log(f"전환점 {len(filtered)}개 확정 (최대 {max_points}개 제한)")
    return filtered