import time
from config import settings   # Settings() 객체

DEBUG = settings.DEBUG
LOG_LLM_RESPONSES = settings.LOG_LLM_RESPONSES

def log(msg: str) -> None:
    if DEBUG:
        print(msg)

def log_raw_llm_response(raw: str, log_file: str = "llm_raw_responses.log") -> None:
    if not LOG_LLM_RESPONSES:
        return
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print("=== LLM RAW RESPONSE START ===")
    print(raw)
    print("=== LLM RAW RESPONSE END ===\n")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- {stamp} ---\n{raw}\n--- END RESPONSE ---\n")