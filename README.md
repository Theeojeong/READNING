# Readning
# 🎵 Readning - 감정 기반 AI 음악 생성 API

텍스트를 입력하면 감정 흐름을 분석해, 해당 분위기에 맞는 음악을 생성하고 결합하여 완성된 트랙을 제공합니다.

- 감정 기반 문장 분할 (감정 청킹)
- LLM 기반 음악 프롬프트 생성 (global + regional)
- Meta MusicGen으로 음악 생성
- FastAPI로 API 구성, Swagger UI 제공

---

## 🛠 기술 스택

- Python 3.9
- FastAPI
- Transformers (감정 분석)
- Ollama (프롬프트 생성)
- Audiocraft / MusicGen
- Pydub (오디오 병합)
- Uvicorn (서버 실행)

---

## 🚀 설치 및 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

혹은 직접 설치

1. pip install pydantic_settings audiocraft fastapi ollama nltk torchaudio numpy==1.26.3
2. sudo apt-get update
3. sudo apt-get install ffmpeg -y


# 1-1 ollama 서버 실행 및 모델 다운로드

a. curl -fsSL https://ollama.com/install.sh | sh
b. .py 파일 생성 후 아래 내용 복붙 및 실행
import subprocess
import time

# Ollama 서버를 백그라운드에서 실행합니다.
# stdout과 stderr는 필요한 경우 캡처할 수 있습니다.
proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 서버가 완전히 시작될 때까지 잠시 대기 (예: 5초)
time.sleep(5)

print("Ollama server launched with PID:", proc.pid)

c. 다른 터미널에서 ollama pull gemma3:4b 실행

# 2. 서버 실행 ### 변경 가능성 있음
uvicorn main:app --reload --root-path /proxy/8000
혹은
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --root-path /proxy/8000

# 3. Swagger UI 접속
http://localhost:8000/docs
```

---

## 📂 디렉토리 구조

```
.
├── main.py                      # FastAPI 앱 실행 파일
├── config.py                   # 경로 및 설정 상수
├── routers/
│   └── musicgen_upload_router.py
├── services/
│   ├── prompt_service.py
│   ├── musicgen_service.py
│   ├── emotion_service.py
│   └── merge_service.py
├── utils/
│   └── file_utils.py
├── gen_muscis/                  # 생성된 음원 저장 경로
├── requirements.txt
└── README.md
```

---

## 📡 API 개요

### POST /generate/music
- .txt 파일 업로드
- 음악 생성 → 병합
- 응답으로 다운로드 링크 반환

### GET /download
- 최종 생성된 `final_mix.wav` 다운로드

---

## 🔮 향후 개발 예정
2025/04/22 [ Updated ]
- 사용자별 세션 구분 및 저장 분리
- PDF파일 처리, 챕터별 다운로드 API 구분
- 음악 생성 비동기 처리 ( 최적화 ) 
- Dokerlize

---



