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

def get_emotion_analysis_prompt(segment: str) -> str:
    return f"""
You are assisting an audio-engine pipeline that adds background music to a story.
Your task is to detect emotionally meaningful turning points so the music can change
exactly when the reader's feelings shift.

⚠️  Output MUST be a single valid JSON object (NO markdown), or:
     {{"emotional_phases":[]}} if you cannot comply.

For each turning point include:
- start_text       : a short quotation (≤ 60 chars) starting at the transition
- emotions_before  : main feelings just BEFORE (comma-separated, ≤ 3)
- emotions_after   : main feelings just AFTER  (comma-separated, ≤ 3)
- significance     : 1 (low) to 5 (high) — how strongly the reader’s emotion changes
- explanation      : 1 short sentence (≤ 25 words) why this moment matters musically

TEXT SEGMENT (max 2600 chars):
{segment}

Return exactly ONE JSON in this schema:
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

# def get_emotion_analysis_prompt(segment: str) -> str:
#     return f"""
# You must return a SINGLE JSON object describing emotional phases in valid JSON (no markdown).
# Use only standard double quotes. Return nothing else.
# If you cannot comply, return {{"emotional_phases":[]}}.
# TEXT SEGMENT:
# {segment}
# Return ONE JSON of the form:
# {{
#   "emotional_phases":[
#     {{
#       "start_text":"",
#       "emotions_before":"",  
#       "emotions_after":"",  
#       "significance":0,       
#       "explanation":""        
#     }}
#   ]
# }}
# """.strip()