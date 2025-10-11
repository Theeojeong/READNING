import json
import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from utils.logger import log, log_raw_llm_response
from services.get_emotion_analysis_prompt import get_emotion_analysis_prompt
from services.clean_json import clean_json
from services.model_manager import ollama_manager

# <Structured Output을 위한 Pydantic 모델>

class EmotionalPhase(BaseModel):

    position_in_full_text: int = Field(description="전체 텍스트에서의 위치 (문자 인덱스)")
    emotions_before: str = Field(description="전환점 이전의 감정")
    emotions_after: str = Field(description="전환점 이후의 감정")
    significance: int = Field(description="전환점의 중요도 (1-5)", ge=1, le=5)
    explanation: str = Field(description="전환점에 대한 설명")
    start_text: str = Field(description="전환점 시작 부분의 텍스트 (최대 100자)")

class EmotionAnalysisResult(BaseModel):

    emotional_phases: List[EmotionalPhase] = Field(description="감정 전환점 리스트")

# <감정 분석 호출>
# 한 청크(segment)를 LLM 에 보내서
# ──▶ 감정 전환점 JSON { "emotional_phases":[ … ] }  를 받아오는 함수.
# • 최대 3 회 재시도 → 네트워크 오류·JSON 파싱 오류 대비
# • 실패 시 {"emotional_phases":[]}  빈 결과 반환
def analyze_emotions_with_gpt(segment: str) -> Dict[str, Any]:
    """Structured Output을 사용한 감정 분석"""
    log(f"분석 요청: {len(segment)}자")
    prompt = get_emotion_analysis_prompt(segment)

    for attempt in range(3):
        try:
            # Structured Output 사용
            result = ollama_manager.chat_with_structured_output(
                [{"role": "user", "content": prompt}],
                EmotionAnalysisResult
            )
            
            # Pydantic 모델을 dict로 변환
            result_dict = result.model_dump()
            log(f"✅ Structured Output 분석 성공: {len(result_dict.get('emotional_phases', []))}개 전환점")
            return result_dict
            
        except Exception as e:
            log(f"Structured Output 분석 오류({attempt+1}/3): {e}")
            
            # Fallback: 기존 방식으로 재시도
            try:
                resp = ollama_manager.chat([{"role": "user", "content": prompt}])
                raw = resp["message"]["content"].strip()
                log_raw_llm_response(raw)

                js = clean_json(raw)    
                if js and "emotional_phases" in js:
                    log(f"✅ Fallback 분석 성공: {len(js.get('emotional_phases', []))}개 전환점")
                    return js
            except Exception as fallback_e:
                log(f"Fallback 분석도 실패: {fallback_e}")

        log("재시도 중...")
        time.sleep(2 * (attempt + 1))
        
    return {"emotional_phases": []}  # 3 회 모두 실패했으면 빈 구조 반환 (후단 로직이 안전하게 처리)