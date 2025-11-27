from pydantic_settings import BaseSettings

GEN_DURATION = 15  # MusicGen 각 청크 음악 생성 길이 (초)
OUTPUT_DIR = "gen_musics"

# 고정 상수 (성능 최적화)
MAX_SEGMENT_SIZE   = 6000   # LLM 1회 처리 최대 글자수 (num_ctx=2048 토큰에 맞춤)
OVERLAP_SIZE       = 250    # 청크 겹침 길이 (MAX_SEGMENT_SIZE의 10%)
CHUNK_PREVIEW_LEN  = 300    # 디버그용 텍스트 미리보기 길이

# 페이징/동시성 관련 상수
CHUNKS_PER_PAGE = 4                 # 한 페이지당 묶을 청크 수
MAX_CONCURRENT_EMOTION_ANALYSIS = 3 # 감정 분석 동시 실행 수
MAX_CONCURRENT_MUSIC_GENERATION = 1 # MusicGen 동시 실행 수 (모델 제약)

# 감정 분석 및 청크 분할 관련 상수
SIGNIFICANCE_THRESHOLD = 3          # 감정 전환점 중요도 임계값 (1-5, 이 값 이상만 청크 분할)
MIN_CHUNK_SIZE = 50                 # 최소 청크 크기 (문자 수)
MAX_CHUNK_SIZE = 8000               # 최대 청크 크기 (문자 수, 음악 생성 제약)

# 환경별로 바뀔 수 있는 값
class Settings(BaseSettings):
    MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    DEBUG: bool = True
    LOG_LLM_RESPONSES: bool = True
    PRINT_CHUNK_TEXT: bool = True

    class Config:
        env_file = ".env"          # 같은 폴더의 .env 읽어들임
        env_file_encoding = "utf-8"
        extra = "ignore"            # 정의되지 않은 환경변수 무시

settings = Settings()

# 호환용 전역 별칭
MODEL_NAME = settings.MODEL_NAME
OPENAI_API_KEY = settings.OPENAI_API_KEY
DEBUG = settings.DEBUG
LOG_LLM_RESPONSES = settings.LOG_LLM_RESPONSES
PRINT_CHUNK_TEXT = settings.PRINT_CHUNK_TEXT
CHUNK_PREVIEW_LENGTH = CHUNK_PREVIEW_LEN
