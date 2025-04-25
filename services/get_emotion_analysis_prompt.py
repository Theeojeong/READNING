# ──────────────────────────────────────────────────────────────
# <프롬프트 & 파싱>
# llm에게 청크(위에서 분리한 청크)에서 감정선 변화 위치를 찾도록 요청하는 프롬프트
# <동작 원리>
# 1. {segment} 에 청크를 그대로 삽입.
# 2. JSON 스키마 예시를 보여 주어 json 하나만 반환하도록 요구.
#  - start_text         : 감정선 변화 위치 시작 텍스트
#  - emotions_before/after : 감정선 변화 위치 이전/이후 감정
#  - significance       : 1~10 숫자 (전환 강도)
#  - explanation        : 한두 문장 설명
# 3. 반환된 JSON에는 감정선 변화 위치 정보가 포함되어 있음
# ──────────────────────────────────────────────────────────────
import re

def get_emotion_analysis_prompt(segment: str) -> str:
    return f"""
You must return a SINGLE JSON object describing emotional phases in valid JSON (no markdown).
Use only standard double quotes. Return nothing else.
If you cannot comply, return {{"emotional_phases":[]}}.
TEXT SEGMENT:
{segment}
Return ONE JSON of the form:
{{
  "emotional_phases":[
    {{
      "start_text":"",
      "emotions_before":"",  
      "emotions_after":"",  
      "significance":0,       
      "explanation":""        
    }}
  ]
}}
""".strip()