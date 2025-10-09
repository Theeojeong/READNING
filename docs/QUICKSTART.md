# 🚀 Readning MySQL + Dynamic Scrollama 빠른 시작 가이드

청크 기반 텍스트와 음악을 MySQL에 저장하고 동적으로 Scrollama 리더로 표시하는 방법입니다.

---

## 📋 목차

1. [MySQL 설정 및 실행](#1-mysql-설정-및-실행)
2. [FastAPI 서버 실행](#2-fastapi-서버-실행)
3. [음악 생성 및 MySQL 저장](#3-음악-생성-및-mysql-저장)
4. [동적 리더 페이지 접속](#4-동적-리더-페이지-접속)
5. [API 문서](#5-api-문서)

---

## 1. MySQL 설정 및 실행

### ✅ Docker로 MySQL 실행

```powershell
# MySQL + phpMyAdmin 실행
docker-compose up -d

# 상태 확인
docker ps

# 로그 확인
docker-compose logs -f mysql
```

### ✅ MySQL 접속 확인

**방법 1: 터미널**
```powershell
docker exec readning-mysql mysql -u root -preadning2024 -e "SHOW DATABASES;"
```

**방법 2: phpMyAdmin 웹 UI**
- http://localhost:8080 접속
- 서버: `mysql`
- 사용자: `root`
- 비밀번호: `readning2024`

**방법 3: Python 테스트**
```powershell
python test_mysql_connection.py
```

---

## 2. FastAPI 서버 실행

### ✅ 환경 설정

`.env` 파일 생성 (프로젝트 루트):
```env
DATABASE_URL=mysql+pymysql://readning_user:readning_pass@localhost:3307/readning
OUTPUT_DIR=gen_musics
```

### ✅ 서버 실행

```powershell
# 가상환경 활성화 (선택사항)
# python -m venv venv
# .\venv\Scripts\activate

# FastAPI 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ✅ API 문서 확인

브라우저에서 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 3. 음악 생성 및 MySQL 저장

### ✅ API 호출 예시 (Python)

```python
import requests

# 텍스트 파일 준비
with open('sample.txt', 'w', encoding='utf-8') as f:
    f.write("""
    새로운 하루가 시작됩니다. 창밖으로 부드러운 햇살이 들어오고, 
    새들의 지저귐이 들립니다. 오늘은 어떤 이야기를 만들어갈까요?
    
    첫 발걸음을 내딛습니다. 길은 때로는 평탄하고, 때로는 험난합니다.
    하지만 모든 순간이 의미 있는 경험이 됩니다.
    """)

# API 호출
url = 'http://localhost:8000/generate/music-v3-long'
files = {'file': open('sample.txt', 'rb')}
data = {
    'user_id': 'test_user',
    'book_title': 'my_novel',
    'page': 1,
    'target_len': 240  # 음악 길이 (초)
}

response = requests.post(url, files=files, data=data)
print(response.json())

# 응답 예시:
# {
#     "message": "my_novel p1 음원 생성 완료",
#     "download_url": "/gen_musics/test_user/my_novel/ch1.wav",
#     "page": 1,
#     "chunks": 5
# }
```

### ✅ cURL로 호출

```bash
curl -X POST "http://localhost:8000/generate/music-v3-long" \
  -F "file=@sample.txt" \
  -F "user_id=test_user" \
  -F "book_title=my_novel" \
  -F "page=1" \
  -F "target_len=240"
```

### ✅ MySQL에 저장된 데이터 확인

**phpMyAdmin에서:**
1. http://localhost:8080 접속
2. `readning` 데이터베이스 선택
3. `books`, `chapters`, `chunks` 테이블 확인

**Python으로:**
```python
from services.mysql_service import mysql_service

data = mysql_service.get_chapter_chunks("test_user_my_novel", 1)
print(data)
```

---

## 4. 동적 리더 페이지 접속

### ✅ 로컬 파일로 접속

```
scrollama/dynamic-reader.html?user_id=test_user&book_title=my_novel&page=1
```

브라우저에서 파일 직접 열기:
```
file:///C:/Readning/scrollama/dynamic-reader.html?user_id=test_user&book_title=my_novel&page=1
```

### ✅ 작동 방식

1. URL 파라미터에서 `user_id`, `book_title`, `page` 읽기
2. FastAPI `/api/reader` 엔드포인트 호출
3. MySQL에서 청크 + 음악 데이터 조회
4. 동적으로 Scrollama `.step` 요소 생성
5. 스크롤 시 해당 청크의 음악 자동 재생

### ✅ 테스트 데이터로 확인

```python
# test_reader.py
import webbrowser
import subprocess
import time

# 1) FastAPI 서버 시작 (백그라운드)
# subprocess.Popen(['uvicorn', 'main:app', '--reload'])
# time.sleep(3)

# 2) 브라우저 열기
url = "file:///C:/Readning/scrollama/dynamic-reader.html?user_id=test_user&book_title=test_book&page=1"
webbrowser.open(url)
```

---

## 5. API 문서

### ✅ 음악 생성 API

**Endpoint:** `POST /generate/music-v3-long`

**Parameters:**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `file` | File | 텍스트 파일 (UTF-8) |
| `user_id` | string | 사용자 ID |
| `book_title` | string | 책 제목 (URL safe) |
| `page` | int | 페이지 번호 |
| `target_len` | int | 음악 길이 (초, 기본값: 240) |

**Response:**
```json
{
  "message": "my_novel p1 음원 생성 완료",
  "download_url": "/gen_musics/test_user/my_novel/ch1.wav",
  "page": 1,
  "chunks": 5
}
```

---

### ✅ 청크 조회 API

**Endpoint:** `GET /api/reader/{user_id}/{book_title}/{page}`

**Example:** 
```
GET http://localhost:8000/api/reader/test_user/my_novel/1
```

**Response:**
```json
{
  "page": 1,
  "bookId": "test_user_my_novel",
  "totalDuration": 240,
  "createdAt": "2025-10-07T14:30:00",
  "chunks": [
    {
      "index": 1,
      "fullText": "새로운 하루가 시작됩니다...",
      "text": "새로운 하루가 시작됩니다... (500자 미리보기)",
      "emotion": "peaceful",
      "audioUrl": "/gen_musics/test_user/my_novel/chunk_1.wav",
      "duration": 30.0
    },
    {
      "index": 2,
      "fullText": "첫 발걸음을 내딛습니다...",
      "text": "첫 발걸음을 내딛습니다...",
      "emotion": "adventurous",
      "audioUrl": "/gen_musics/test_user/my_novel/chunk_2.wav",
      "duration": 30.0
    }
  ]
}
```

---

### ✅ 챕터 목록 조회 API

**Endpoint:** `GET /api/reader/{user_id}/{book_title}`

**Example:**
```
GET http://localhost:8000/api/reader/test_user/my_novel
```

**Response:**
```json
{
  "bookId": "test_user_my_novel",
  "chapters": [
    {
      "page": 1,
      "totalDuration": 240,
      "chunkCount": 5,
      "createdAt": "2025-10-07T14:30:00"
    },
    {
      "page": 2,
      "totalDuration": 180,
      "chunkCount": 3,
      "createdAt": "2025-10-07T15:00:00"
    }
  ]
}
```

---

### ✅ 헬스체크 API

**Endpoint:** `GET /api/reader/health`

**Response:**
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

## 🔧 문제 해결

### MySQL 연결 실패
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```
**해결:**
1. Docker 컨테이너 실행 확인: `docker ps`
2. 포트 확인: `3307` (기본값이 아님)
3. `.env` 파일 확인

### 포트 충돌
```
Ports are not available: exposing port TCP 0.0.0.0:3306
```
**해결:**
`docker-compose.yml`에서 포트를 `3307:3306`으로 변경 (이미 적용됨)

### 음악 파일 404 에러
```
GET /gen_musics/test_user/my_novel/chunk_1.wav -> 404
```
**해결:**
1. 음악 생성 API 먼저 호출
2. `gen_musics/` 폴더 권한 확인
3. FastAPI static files 마운트 확인

---

## 🎯 다음 단계

1. ✅ **프론트엔드 React 통합**
   - `dynamic-reader.html`을 React 컴포넌트로 변환
   - `frontend/src/pages/ReaderPage.tsx`에 통합

2. ✅ **UI 개선**
   - 챕터 네비게이션 추가
   - 북마크 기능
   - 읽기 진행률 표시

3. ✅ **AWS 배포**
   - EC2: FastAPI 서버
   - RDS: MySQL 데이터베이스
   - S3: 음악 파일 저장
   - CloudFront: CDN

4. ✅ **성능 최적화**
   - 음악 파일 압축
   - 청크 캐싱
   - lazy loading

---

## 📚 참고 문서

- [MySQL 설정 가이드](MYSQL_SETUP.md)
- [Scrollama 공식 문서](https://github.com/russellsamora/scrollama)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)

---

**문제가 있으신가요?**
- Discord: [Readning 커뮤니티]
- GitHub Issues: [프로젝트 저장소]

**Happy Reading! 📖🎵**

