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

# 2. 서버 실행 ### 변경 가능성 있음
uvicorn main:app --reload

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



