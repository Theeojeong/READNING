import json
import time
import ollama
from typing import Dict, Any
from utils.logger import log, log_raw_llm_response
from config import MODEL_NAME
from services.get_emotion_analysis_prompt import get_emotion_analysis_prompt
from services.sanitize_llm_output import sanitize_llm_output

# ──────────────────────────────────────────────────────────────
# <감정 분석 호출>
# 한 청크(segment)를 LLM 에 보내서
# ──▶ 감정 전환점 JSON { "emotional_phases":[ … ] }  를 받아오는 함수.
# • 최대 3 회 재시도 → 네트워크 오류·JSON 파싱 오류 대비
# • 실패 시 {"emotional_phases":[]}  빈 결과 반환
# ──────────────────────────────────────────────────────────────
def analyze_emotions_with_gpt(segment: str) -> Dict[str, Any]:

    log(f"분석 요청: {len(segment)}자")
    prompt = get_emotion_analysis_prompt(segment)
    for attempt in range(3):
        try:
            resp = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
            raw = resp["message"]["content"].strip()
            log_raw_llm_response(raw)
            cleaned = sanitize_llm_output(raw)
            try:
                js = json.loads(cleaned)
                if "emotional_phases" in js:
                    return js
            except json.JSONDecodeError:
                pass
        except Exception as e:
            log(f"분석 오류({attempt+1}/3): {e}")
        log("재시도 중...")
        time.sleep(2 * (attempt + 1))
    return {"emotional_phases": []}  # 3 회 모두 실패했으면 빈 구조 반환 (후단 로직이 안전하게 처리)