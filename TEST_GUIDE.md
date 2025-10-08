# 🧪 Readning 웹 테스트 가이드

준비한 텍스트 파일로 음악 생성 및 동적 리더를 테스트하는 방법입니다.

---

## 📋 사전 준비

### ✅ 체크리스트
- [x] MySQL 실행 중 (`docker ps` 확인)
- [ ] Python 3.11 환경
- [ ] 의존성 설치 완료
- [ ] 테스트용 텍스트 파일 준비

---

## 🚀 Step 1: 서버 시작

### 1-1. 의존성 설치 (처음 한 번만)
```bash
# uv 사용 시
uv sync

# 또는 pip 사용 시
pip install -r requirements.txt
```

### 1-2. FastAPI 서버 시작
```bash
uvicorn main:app --reload --port 8000
```

**성공 메시지:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🌐 Step 2: 테스트 페이지 접속

브라우저에서 다음 URL을 엽니다:

```
http://localhost:8000/static/upload-and-test.html
```

---

## 📝 Step 3: 텍스트 파일 업로드

### 3-1. 페이지에서 입력

| 항목 | 입력 예시 | 설명 |
|------|----------|------|
| **텍스트 파일** | `sample.txt` | 준비한 책 텍스트 파일 |
| **사용자 ID** | `test_user` | 임의의 사용자 ID |
| **책 제목** | `my_novel` | 영문/숫자로 (공백 없이) |
| **페이지 번호** | `1` | 1부터 시작 |
| **음악 길이** | `240` | 초 단위 (기본 4분) |

### 3-2. "음악 생성하기" 클릭

⏳ **처리 시간:** 약 1-5분 소요
- 텍스트 분석
- 감정 기반 청크 분할
- 각 청크별 음악 생성 (MusicGen)
- MySQL 저장

### 3-3. 완료 확인

✅ 성공 시 메시지:
```
✅ 음악 생성 완료!
📊 생성된 청크: 5개
📖 책 ID: test_user_my_novel
📄 페이지: 1
```

---

## 🎬 Step 4: 동적 리더에서 확인

### 4-1. "리더 페이지 열기" 클릭

새 탭에서 Scrollama 동적 리더가 열립니다.

### 4-2. 리더 사용법

- **스크롤**: 아래로 스크롤하면 다음 청크로 이동
- **음악 재생**: 각 청크에 도달하면 자동으로 음악 전환
- **수동 재생**: 오른쪽 오디오 플레이어에서 재생/일시정지

### 4-3. 확인 사항

✅ **정상 작동:**
- 청크별로 다른 텍스트 표시
- 청크별로 다른 감정 배지 (peaceful, adventurous 등)
- 스크롤 시 음악 자동 전환
- 오디오 플레이어에서 수동 컨트롤 가능

---

## 🏥 Step 5: 시스템 상태 확인

테스트 페이지에서 "헬스체크 실행" 클릭

### 확인 항목

| 항목 | 상태 | 의미 |
|------|------|------|
| **mysql** | ✅ ok | 데이터베이스 연결 정상 |
| **disk** | ✅ ok | 디스크 여유 공간 충분 |
| **musicgen** | ✅ ok | AI 모델 로드 완료 |
| **output_dir** | ✅ ok | 출력 디렉토리 존재 |

---

## 📊 생성된 파일 확인

### 디렉토리 구조

```
gen_musics/
└── test_user/
    └── my_novel/
        ├── chunk_1.wav  (30초)
        ├── chunk_2.wav  (30초)
        ├── chunk_3.wav  (30초)
        ├── chunk_4.wav  (30초)
        └── chunk_5.wav  (30초)
```

### MySQL 데이터 확인

```bash
# phpMyAdmin 접속
http://localhost:8080

# 또는 Python 스크립트
python test_mysql_connection.py
```

---

## 🐛 문제 해결

### 1. "서버에 연결할 수 없습니다"

**원인:** FastAPI 서버가 실행되지 않음

**해결:**
```bash
uvicorn main:app --reload --port 8000
```

---

### 2. "MySQL 연결 실패"

**원인:** MySQL 컨테이너가 실행되지 않음

**해결:**
```bash
docker-compose up -d
docker ps  # 확인
```

---

### 3. "음악 생성 중 오류"

**원인:** MusicGen 모델 로딩 실패 또는 메모리 부족

**확인:**
```bash
# 헬스체크 API 호출
curl http://localhost:8000/generate/health
```

**해결:**
- GPU 메모리 확인 (`nvidia-smi`)
- 모델 다운로드 대기 (첫 실행 시 시간 소요)
- 청크 길이 조정 (텍스트를 짧게)

---

### 4. "리더 페이지에서 음악이 재생되지 않음"

**원인:** 브라우저 자동 재생 정책

**해결:**
- 페이지 로드 후 "클릭하여 오디오 자동 재생 시작" 버튼 클릭
- 또는 오디오 플레이어에서 수동 재생

---

### 5. "청크가 표시되지 않음"

**원인:** API 응답 오류 또는 CORS 문제

**확인:**
```bash
# 브라우저 개발자 도구 (F12) → Console 확인
# Network 탭에서 API 응답 확인
```

**해결:**
- 올바른 URL 사용 (`http://localhost:8000`)
- CORS 설정 확인 (main.py)

---

## 🎯 테스트 시나리오

### 시나리오 1: 짧은 텍스트
```
파일: 500자 이하
예상: 1-2개 청크, 1분 내 완료
```

### 시나리오 2: 중간 텍스트
```
파일: 1,000-5,000자
예상: 3-7개 청크, 2-3분 소요
```

### 시나리오 3: 긴 텍스트
```
파일: 10,000자 이상
예상: 10-15개 청크, 3-5분 소요
```

---

## 📸 스크린샷 예시

### 업로드 페이지
```
[파일 선택] → [정보 입력] → [음악 생성하기]
          ↓
    [생성 중... 1-5분]
          ↓
    ✅ 음악 생성 완료!
          ↓
    [리더 페이지 열기]
```

### 동적 리더
```
┌─────────────────────────────────────┐
│  Chunk 1: peaceful                  │
│  새로운 하루가 시작됩니다...        │
│                                     │
│  [스크롤]                           │
│                                     │
│  Chunk 2: adventurous               │
│  첫 발걸음을 내딛습니다...          │
└─────────────────────────────────────┘

      [오디오 플레이어] →
```

---

## 🔗 유용한 링크

| 링크 | 설명 |
|------|------|
| http://localhost:8000/docs | Swagger API 문서 |
| http://localhost:8000/static/upload-and-test.html | 테스트 페이지 |
| http://localhost:8000/generate/health | 헬스체크 API |
| http://localhost:8080 | phpMyAdmin (MySQL) |
| http://localhost:8000/scrollama/dynamic-reader.html | 동적 리더 (직접 접속) |

---

## 📝 테스트 결과 기록

### 체크리스트

- [ ] 파일 업로드 성공
- [ ] 음악 생성 완료 (청크 개수 확인)
- [ ] MySQL에 데이터 저장됨
- [ ] 리더 페이지에서 청크 표시됨
- [ ] 음악 자동 재생 작동
- [ ] 스크롤 시 음악 전환 작동
- [ ] 헬스체크 모두 OK

### 성능 측정

| 항목 | 값 |
|------|-----|
| 텍스트 길이 | _____자 |
| 청크 개수 | _____개 |
| 음악 생성 시간 | _____분 |
| 첫 로드 시간 | _____초 |

---

**Happy Testing! 🎉**

궁금한 점이 있으면 언제든지 물어보세요!

