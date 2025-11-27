"""
RAG 시스템 유틸리티 함수들
"""

from typing import List, Dict, Any
import re
from pathlib import Path


def load_text_from_file(file_path: str) -> str:
    """
    파일에서 텍스트를 로드합니다.

    Args:
        file_path: 파일 경로

    Returns:
        텍스트 내용
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # UTF-8 실패 시 다른 인코딩 시도
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                return f.read()
        except:
            raise ValueError(f"파일을 읽을 수 없습니다: {file_path}")


def save_chunks_to_json(chunks: List[Any], output_path: str) -> None:
    """
    청크를 JSON 파일로 저장합니다.

    Args:
        chunks: EmotionChunk 객체 리스트
        output_path: 저장할 파일 경로
    """
    import json

    chunks_data = [
        chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
        for chunk in chunks
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 청크 저장 완료: {output_path}")


def load_chunks_from_json(json_path: str) -> List[Dict[str, Any]]:
    """
    JSON 파일에서 청크를 로드합니다.

    Args:
        json_path: JSON 파일 경로

    Returns:
        청크 딕셔너리 리스트
    """
    import json

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_text(text: str) -> str:
    """
    텍스트를 정제합니다.

    Args:
        text: 원본 텍스트

    Returns:
        정제된 텍스트
    """
    # 연속된 공백 제거
    text = re.sub(r'\s+', ' ', text)

    # 연속된 줄바꿈을 2개로 제한
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    텍스트를 문장 단위로 분할합니다.

    Args:
        text: 전체 텍스트

    Returns:
        문장 리스트
    """
    # 한글/영어 문장 구분
    sentence_endings = r'[.!?。!?]\s+'
    sentences = re.split(sentence_endings, text)

    return [s.strip() for s in sentences if s.strip()]


def calculate_chunk_overlap(
    chunks: List[Any],
    overlap_chars: int = 50
) -> List[Dict[str, Any]]:
    """
    청크 간 오버랩을 계산합니다.

    Args:
        chunks: 청크 리스트
        overlap_chars: 오버랩할 문자 수

    Returns:
        오버랩 정보가 추가된 청크 리스트
    """
    result = []

    for i, chunk in enumerate(chunks):
        chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
        chunk_dict['overlap_info'] = {
            'has_prev': i > 0,
            'has_next': i < len(chunks) - 1
        }

        if i > 0:
            prev_chunk = chunks[i - 1]
            prev_text = prev_chunk.text if hasattr(prev_chunk, 'text') else prev_chunk.get('text', '')
            chunk_dict['overlap_info']['prev_overlap'] = prev_text[-overlap_chars:]

        if i < len(chunks) - 1:
            next_chunk = chunks[i + 1]
            next_text = next_chunk.text if hasattr(next_chunk, 'text') else next_chunk.get('text', '')
            chunk_dict['overlap_info']['next_overlap'] = next_text[:overlap_chars]

        result.append(chunk_dict)

    return result


def merge_search_results(
    results1: List[Dict[str, Any]],
    results2: List[Dict[str, Any]],
    weight1: float = 0.5,
    weight2: float = 0.5
) -> List[Dict[str, Any]]:
    """
    두 검색 결과를 가중치 기반으로 병합합니다.

    Args:
        results1: 첫 번째 검색 결과
        results2: 두 번째 검색 결과
        weight1: 첫 번째 결과의 가중치
        weight2: 두 번째 결과의 가중치

    Returns:
        병합된 검색 결과
    """
    # ID 기반 결과 매핑
    merged_dict = {}

    for result in results1:
        result_id = result.get('id', '')
        if result_id:
            merged_dict[result_id] = result.copy()
            merged_dict[result_id]['merged_score'] = result.get('distance', 0) * weight1

    for result in results2:
        result_id = result.get('id', '')
        if result_id:
            if result_id in merged_dict:
                # 기존 결과와 병합
                merged_dict[result_id]['merged_score'] += result.get('distance', 0) * weight2
            else:
                # 새 결과 추가
                merged_dict[result_id] = result.copy()
                merged_dict[result_id]['merged_score'] = result.get('distance', 0) * weight2

    # 병합된 스코어로 정렬
    merged_results = list(merged_dict.values())
    merged_results.sort(key=lambda x: x.get('merged_score', 0))

    return merged_results


def get_emotion_statistics(chunks: List[Any]) -> Dict[str, Any]:
    """
    청크들의 감정 통계를 계산합니다.

    Args:
        chunks: EmotionChunk 객체 리스트

    Returns:
        통계 딕셔너리
    """
    if not chunks:
        return {"total": 0}

    emotions = []
    significances = []
    total_length = 0

    for chunk in chunks:
        if hasattr(chunk, 'emotion'):
            emotions.append(chunk.emotion)
            total_length += len(chunk.text)

            if hasattr(chunk, 'metadata') and chunk.metadata:
                sig = chunk.metadata.get('transition_significance')
                if sig:
                    significances.append(sig)
        elif isinstance(chunk, dict):
            emotions.append(chunk.get('emotion', 'unknown'))
            total_length += len(chunk.get('text', ''))

            sig = chunk.get('metadata', {}).get('transition_significance')
            if sig:
                significances.append(sig)

    # 감정 분포
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    stats = {
        "total_chunks": len(chunks),
        "total_characters": total_length,
        "avg_chunk_length": total_length / len(chunks) if chunks else 0,
        "emotion_distribution": emotion_counts,
    }

    if significances:
        stats["avg_significance"] = sum(significances) / len(significances)
        stats["max_significance"] = max(significances)
        stats["transition_points"] = len(significances)

    return stats


def visualize_emotional_arc(chunks: List[Any]) -> str:
    """
    감정 아크를 텍스트 기반으로 시각화합니다.

    Args:
        chunks: EmotionChunk 객체 리스트

    Returns:
        시각화 텍스트
    """
    if not chunks:
        return "청크가 없습니다."

    lines = ["감정 흐름 시각화:", "=" * 50]

    for i, chunk in enumerate(chunks):
        emotion = chunk.emotion if hasattr(chunk, 'emotion') else chunk.get('emotion', 'unknown')
        text_preview = (chunk.text if hasattr(chunk, 'text') else chunk.get('text', ''))[:30]

        # 감정 이모지 매핑
        emotion_emoji = {
            "기쁨": "😊",
            "슬픔": "😢",
            "분노": "😠",
            "두려움": "😨",
            "놀람": "😲",
            "혐오": "😖",
            "neutral": "😐"
        }

        emoji = emotion_emoji.get(emotion, "❓")

        line = f"{i+1:3d}. {emoji} {emotion:10s} | {text_preview}..."

        # 전환점 표시
        if hasattr(chunk, 'metadata') and chunk.metadata:
            if chunk.metadata.get('is_transition_point'):
                sig = chunk.metadata.get('transition_significance', 0)
                line += f" [전환점 ★x{sig}]"

        lines.append(line)

    lines.append("=" * 50)
    return "\n".join(lines)


def benchmark_chunking_strategies(
    text: str,
    strategies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    여러 청킹 전략을 벤치마크합니다.

    Args:
        text: 테스트 텍스트
        strategies: 전략 설정 리스트
                   [{"name": "strategy1", "params": {...}}, ...]

    Returns:
        벤치마크 결과
    """
    import time
    from .emotion_chunker import split_text_by_emotions

    results = {}

    for strategy in strategies:
        name = strategy.get("name", "unknown")
        params = strategy.get("params", {})

        start_time = time.time()

        try:
            chunks = split_text_by_emotions(text, **params)
            elapsed = time.time() - start_time

            stats = get_emotion_statistics(chunks)
            stats["execution_time"] = elapsed
            stats["strategy_name"] = name

            results[name] = stats

        except Exception as e:
            results[name] = {"error": str(e)}

    return results
