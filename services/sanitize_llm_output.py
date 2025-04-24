import re

def sanitize_llm_output(raw: str) -> str:
    """
    LLM 응답에서 JSON 부분만 깨끗하게 뽑아낸 뒤
    파싱에 방해되는 특수문자를 교정한다.
    """
    # 0) ```json ... ``` 코드블록 추출
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
    if code_block:
        raw = code_block.group(1)

    # 1) 스마트따옴표·홑따옴표 → ASCII "
    smart_quotes = {
        "“": "\"", "”": "\"", "„": "\"", "‟": "\"",
        "‘": "\"", "’": "\"", "‚": "\"", "‛": "\"",
    }
    for bad, good in smart_quotes.items():
        raw = raw.replace(bad, good)

    # 2) 줄바꿈 · 탭 → 공백 1칸
    raw = re.sub(r'[\t\r\n]+', ' ', raw)

    # 3) 제어문자(0x00-0x1F) 제거
    raw = re.sub(r'[\x00-\x1F]+', '', raw)

    # 4) 마지막 쉼표 제거  {"a":1,}  [1,2,]
    raw = re.sub(r',\s*([}\]])', r'\1', raw)

    # 5) 혹시 남은 백틱 제거
    raw = raw.replace('```', '').strip()

    return raw