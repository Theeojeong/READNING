# pip install pydantic-settings
from pydantic_settings import BaseSettings

OUTPUT_DIR = "gen_musics"
GEN_DURATION = 15
TOTAL_DURATION = 120
FINAL_MIX_NAME = "final_mix.wav"

# ── 고정 상수 ─────────────────────────────
MAX_SEGMENT_SIZE   = 6000   # LLM 1회 처리 최대 글자수
OVERLAP_SIZE       = 600    # 청크 겹침 길이
CHUNK_PREVIEW_LEN  = 300    # 디버그용 텍스트 미리보기 길이

# ── 환경별로 바뀔 수 있는 값 ───────────────
class Settings(BaseSettings):
    MODEL_NAME: str = "gemma3:4b"
    DEBUG: bool = True
    LOG_LLM_RESPONSES: bool = True
    PRINT_CHUNK_TEXT: bool = True
    # Firebase 연동용 경로 및 버킷 (선택 사항)
    firebase_sa_path: str | None = None
    firebase_bucket: str | None = None

    class Config:
        env_file = ".env"          # 같은 폴더의 .env 읽어들임
        env_file_encoding = "utf-8"
        extra = "ignore"            # 정의되지 않은 환경변수 무시

settings = Settings()

# ---- 호환용 전역 별칭 ----
MODEL_NAME = settings.MODEL_NAME
DEBUG = settings.DEBUG
LOG_LLM_RESPONSES = settings.LOG_LLM_RESPONSES
PRINT_CHUNK_TEXT = settings.PRINT_CHUNK_TEXT
CHUNK_PREVIEW_LENGTH = CHUNK_PREVIEW_LEN
