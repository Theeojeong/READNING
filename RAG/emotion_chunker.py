"""
감정 기반 의미론적 청킹 모듈

텍스트를 감정 전환점을 기준으로 의미 있는 청크로 분할합니다.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from utils.logger import log
from services.analyze_emotions_with_gpt import analyze_emotions_with_gpt


@dataclass
class EmotionChunk:
    """감정 기반 청크 데이터 클래스"""
    text: str
    emotion: str
    start_pos: int
    end_pos: int
    chunk_id: int
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "text": self.text,
            "emotion": self.emotion,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata or {}
        }


def split_text_by_emotions(
    text: str,
    max_chunk_size: int = 2000,
    min_chunk_size: int = 100,
    overlap_size: int = 50
) -> List[EmotionChunk]:
    """
    감정 전환점을 기준으로 텍스트를 청킹합니다.

    Args:
        text: 전체 텍스트
        max_chunk_size: 청크 최대 크기 (문자 수)
        min_chunk_size: 청크 최소 크기 (문자 수)
        overlap_size: 청크 간 오버랩 크기

    Returns:
        EmotionChunk 객체 리스트
    """
    log(f"📊 감정 기반 청킹 시작: 텍스트 길이 {len(text)}자")

    # 1. 감정 분석 실행
    analysis_result = analyze_emotions_with_gpt(text)
    phases = analysis_result.get("emotional_phases", [])

    log(f"🔍 감정 전환점 {len(phases)}개 발견")

    if not phases:
        # 전환점이 없으면 문장 단위 폴백
        log("⚠️ 감정 전환점 없음 → 문장 단위 분할로 폴백")
        return _fallback_sentence_split(text, max_chunk_size, overlap_size)

    # 2. 전환점 위치로 청크 경계 설정
    chunks = []
    prev_position = 0
    chunk_id = 0

    for i, phase in enumerate(phases):
        position = phase.get("position_in_full_text")

        if position is None or position <= prev_position:
            log(f"⚠️ 유효하지 않은 위치: {position} (이전: {prev_position})")
            continue

        # 문장 경계로 조정 (문장 중간에서 자르지 않기)
        adjusted_position = _find_sentence_boundary(text, position)

        # 이전 위치부터 현재 전환점까지를 하나의 청크로
        chunk_start = max(0, prev_position - overlap_size) if prev_position > 0 else 0
        chunk_text = text[chunk_start:adjusted_position].strip()

        if len(chunk_text) >= min_chunk_size:
            # 너무 크면 다시 분할
            if len(chunk_text) > max_chunk_size:
                log(f"📦 큰 청크 분할: {len(chunk_text)}자 → {max_chunk_size}자 단위")
                sub_chunks = _split_large_chunk(
                    chunk_text,
                    max_chunk_size,
                    phase.get("emotions_before", "neutral"),
                    chunk_start,
                    chunk_id
                )
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
            else:
                chunk = EmotionChunk(
                    text=chunk_text,
                    emotion=phase.get("emotions_before", "neutral"),
                    start_pos=chunk_start,
                    end_pos=adjusted_position,
                    chunk_id=chunk_id,
                    metadata={
                        "next_emotion": phase.get("emotions_after"),
                        "transition_significance": phase.get("significance"),
                        "transition_explanation": phase.get("explanation"),
                        "is_transition_point": True
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                log(f"✅ 청크 {chunk_id-1}: {len(chunk_text)}자, 감정: {chunk.emotion}")

        prev_position = adjusted_position

    # 마지막 청크 처리
    if prev_position < len(text):
        chunk_start = max(0, prev_position - overlap_size)
        last_chunk_text = text[chunk_start:].strip()

        if len(last_chunk_text) >= min_chunk_size:
            last_emotion = phases[-1].get("emotions_after", "neutral") if phases else "neutral"
            chunk = EmotionChunk(
                text=last_chunk_text,
                emotion=last_emotion,
                start_pos=chunk_start,
                end_pos=len(text),
                chunk_id=chunk_id,
                metadata={"is_last_chunk": True}
            )
            chunks.append(chunk)
            log(f"✅ 마지막 청크 {chunk_id}: {len(last_chunk_text)}자")

    log(f"🎉 청킹 완료: 총 {len(chunks)}개 청크 생성")
    return chunks


def _find_sentence_boundary(text: str, position: int, search_range: int = 100) -> int:
    """
    주어진 위치 근처에서 문장 경계를 찾습니다.

    Args:
        text: 전체 텍스트
        position: 시작 위치
        search_range: 검색 범위

    Returns:
        조정된 위치 (문장 끝)
    """
    # 문장 종결 기호
    sentence_endings = ['. ', '.\n', '! ', '!\n', '? ', '?\n', '。', '! ', '? ', '\n\n']

    # position 근처에서 문장 끝 찾기
    search_start = max(0, position - search_range // 2)
    search_end = min(len(text), position + search_range // 2)
    search_text = text[search_start:search_end]

    # 가장 가까운 문장 끝 찾기
    closest_end = -1
    closest_distance = float('inf')

    for ending in sentence_endings:
        idx = search_text.find(ending, max(0, position - search_start - 20))
        if idx != -1:
            actual_pos = search_start + idx + len(ending)
            distance = abs(actual_pos - position)
            if distance < closest_distance:
                closest_distance = distance
                closest_end = actual_pos

    return closest_end if closest_end != -1 else position


def _split_large_chunk(
    text: str,
    max_size: int,
    emotion: str,
    base_position: int,
    base_chunk_id: int
) -> List[EmotionChunk]:
    """
    큰 청크를 문장 단위로 분할합니다.

    Args:
        text: 분할할 텍스트
        max_size: 최대 크기
        emotion: 해당 청크의 감정
        base_position: 기준 위치
        base_chunk_id: 기준 청크 ID

    Returns:
        분할된 청크 리스트
    """
    # 문장 단위로 분할
    sentences = re.split(r'([.!?。!?]\s+|\n\n)', text)

    chunks = []
    current_chunk = ""
    current_start = 0
    chunk_count = 0

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        separator = sentences[i + 1] if i + 1 < len(sentences) else ""
        full_sentence = sentence + separator

        if len(current_chunk) + len(full_sentence) > max_size and current_chunk:
            # 현재 청크 저장
            chunk = EmotionChunk(
                text=current_chunk.strip(),
                emotion=emotion,
                start_pos=base_position + current_start,
                end_pos=base_position + current_start + len(current_chunk),
                chunk_id=base_chunk_id + chunk_count,
                metadata={"split_from_large_chunk": True}
            )
            chunks.append(chunk)

            current_start += len(current_chunk)
            current_chunk = full_sentence
            chunk_count += 1
        else:
            current_chunk += full_sentence

    # 마지막 청크
    if current_chunk.strip():
        chunk = EmotionChunk(
            text=current_chunk.strip(),
            emotion=emotion,
            start_pos=base_position + current_start,
            end_pos=base_position + current_start + len(current_chunk),
            chunk_id=base_chunk_id + chunk_count,
            metadata={"split_from_large_chunk": True}
        )
        chunks.append(chunk)

    return chunks


def _fallback_sentence_split(
    text: str,
    max_size: int,
    overlap_size: int
) -> List[EmotionChunk]:
    """
    감정 분석 실패 시 폴백: 문장 단위로 분할합니다.

    Args:
        text: 전체 텍스트
        max_size: 최대 크기
        overlap_size: 오버랩 크기

    Returns:
        청크 리스트
    """
    # 문장 단위로 분할
    sentences = re.split(r'([.!?。!?]\s+|\n\n)', text)

    chunks = []
    current_chunk = ""
    current_start = 0
    chunk_id = 0

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        separator = sentences[i + 1] if i + 1 < len(sentences) else ""
        full_sentence = sentence + separator

        if len(current_chunk) + len(full_sentence) > max_size and current_chunk:
            # 현재 청크 저장
            chunk = EmotionChunk(
                text=current_chunk.strip(),
                emotion="neutral",
                start_pos=current_start,
                end_pos=current_start + len(current_chunk),
                chunk_id=chunk_id,
                metadata={"fallback_split": True}
            )
            chunks.append(chunk)

            # 오버랩 처리
            overlap_text = current_chunk[-overlap_size:] if len(current_chunk) > overlap_size else ""
            current_start += len(current_chunk) - len(overlap_text)
            current_chunk = overlap_text + full_sentence
            chunk_id += 1
        else:
            current_chunk += full_sentence

    # 마지막 청크
    if current_chunk.strip():
        chunk = EmotionChunk(
            text=current_chunk.strip(),
            emotion="neutral",
            start_pos=current_start,
            end_pos=len(text),
            chunk_id=chunk_id,
            metadata={"fallback_split": True}
        )
        chunks.append(chunk)

    log(f"📦 폴백 분할 완료: {len(chunks)}개 청크")
    return chunks


def create_overlapping_context(
    chunks: List[EmotionChunk],
    target_chunk_id: int,
    context_window: int = 1
) -> str:
    """
    특정 청크의 앞뒤 문맥을 포함한 텍스트를 생성합니다.

    Args:
        chunks: 전체 청크 리스트
        target_chunk_id: 대상 청크 ID
        context_window: 앞뒤로 포함할 청크 개수

    Returns:
        문맥이 포함된 텍스트
    """
    if not chunks or target_chunk_id >= len(chunks):
        return ""

    start_idx = max(0, target_chunk_id - context_window)
    end_idx = min(len(chunks), target_chunk_id + context_window + 1)

    context_chunks = chunks[start_idx:end_idx]
    return "\n\n".join([chunk.text for chunk in context_chunks])
