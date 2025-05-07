import re
import unicodedata
import json
from utils.logger import log

def clean_json(raw: str) -> dict | None:
    # 1) ``` 블록 제거
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
    raw = (m.group(1) if m else raw).strip()

    # 2) 스마트 따옴표를 ASCII ' 로만 치환 (큰따옴표 X)
    tbl = str.maketrans({'“':"'", '”':"'", '‘':"'", '’':"'"})
    raw = raw.translate(tbl)

    # 3) 제어문자 제거
    raw = "".join(ch for ch in raw if unicodedata.category(ch)[0] != "C")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"JSON 오류: {e}")
        return None