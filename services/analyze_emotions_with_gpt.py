import json
import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from utils.logger import log, log_raw_llm_response
from services.get_emotion_analysis_prompt import get_emotion_analysis_prompt
from services.clean_json import clean_json
from services.model_manager import ollama_manager
from config import SIGNIFICANCE_THRESHOLD

# <Structured Output을 위한 Pydantic 모델>

class EmotionalPhase(BaseModel):
    # Prompt 스키마에 맞춘 필드 구성
    start_text: str = Field(description="전환점 시작 부분의 텍스트 (최대 100자)")
    emotions_before: str = Field(description="전환점 이전의 감정")
    emotions_after: str = Field(description="전환점 이후의 감정")
    significance: int = Field(description="전환점의 중요도 (1-5)", ge=1, le=5)
    explanation: str = Field(description="전환점에 대한 설명")
    position_in_full_text: int | None = Field(default=None, description="전체 텍스트에서의 위치 (문자 인덱스)")

class EmotionAnalysisResult(BaseModel):

    emotional_phases: List[EmotionalPhase] = Field(description="감정 전환점 리스트")

# <감정 분석 호출>
# 한 청크(segment)를 LLM 에 보내서
# ──▶ 감정 전환점 JSON { "emotional_phases":[ … ] }  를 받아오는 함수.
# • 최대 3 회 재시도 → 네트워크 오류·JSON 파싱 오류 대비
# • 실패 시 {"emotional_phases":[]}  빈 결과 반환
def analyze_emotions_with_gpt(segment: str) -> Dict[str, Any]:
    """감정 분석 (LangChain Structured Output 사용)."""
    log(f"🔍 LLM 감정 분석 시작: {len(segment)}자")
    prompt = get_emotion_analysis_prompt(segment)
    log(f"📤 LLM에 프롬프트 전송 중...")

    messages = [{"role": "user", "content": prompt}]
    for attempt in range(3):
        try:
            log(f"🔄 LLM 응답 대기 중... (시도 {attempt+1}/3)")
            result = ollama_manager.chat_with_structured_output(messages, EmotionAnalysisResult)
            phases = result.get("emotional_phases", [])

            # position_in_full_text 자동 계산
            phases_with_positions = _calculate_positions(segment, phases)
            result["emotional_phases"] = phases_with_positions

            # significance 필터링
            filtered_phases = [p for p in phases_with_positions if p.get("significance", 0) >= SIGNIFICANCE_THRESHOLD]

            log(f"✅ LLM 분석 성공: {len(phases)}개 전환점 → {len(filtered_phases)}개 유효 (임계값 {SIGNIFICANCE_THRESHOLD})")

            result["emotional_phases"] = filtered_phases
            return result
        except Exception as e:
            log(f"❌ 분석 오류({attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(1)

    log(f"❌ LLM 분석 최종 실패: 3회 시도 후 실패")
    return {"emotional_phases": []}


def _calculate_positions(segment: str, phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    start_text를 기반으로 position_in_full_text를 자동 계산.

    Args:
        segment: 전체 텍스트 청크
        phases: LLM이 반환한 감정 전환점 리스트

    Returns:
        position_in_full_text가 추가된 phases 리스트
    """
    result_phases = []

    for phase in phases:
        phase_dict = phase if isinstance(phase, dict) else phase.dict()
        start_text = phase_dict.get("start_text", "").strip()

        if not start_text:
            log(f"⚠️ start_text가 비어있음, 위치 계산 불가")
            phase_dict["position_in_full_text"] = None
            result_phases.append(phase_dict)
            continue

        # start_text로 segment에서 위치 찾기
        position = segment.find(start_text)

        if position == -1:
            # 정확히 매칭되지 않으면 앞부분 30자로 재시도
            short_start = start_text[:30]
            position = segment.find(short_start)

            if position == -1:
                log(f"⚠️ 위치 찾기 실패: '{start_text[:50]}...'")
                phase_dict["position_in_full_text"] = None
            else:
                log(f"✅ 부분 매칭으로 위치 찾음: {position}")
                phase_dict["position_in_full_text"] = position
        else:
            phase_dict["position_in_full_text"] = position

        result_phases.append(phase_dict)

    # position 기준으로 정렬 (None은 맨 뒤로)
    result_phases.sort(key=lambda x: x.get("position_in_full_text") if x.get("position_in_full_text") is not None else float('inf'))

    return result_phases