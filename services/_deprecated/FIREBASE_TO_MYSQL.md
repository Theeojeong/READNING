# 🔄 Firebase → MySQL 마이그레이션 완료

## 📋 변경 사항

### ❌ 제거된 것

| 항목 | 위치 | 상태 |
|------|------|------|
| **firestore_service import** | `routers/musicgen_upload_router.py` | ✅ 제거됨 |
| **firebase-admin 의존성** | `pyproject.toml` | ✅ 제거됨 |
| **firestore_service.py** | `services/` → `services/_deprecated/` | ✅ 이동됨 |

### ✅ 유지된 것

| 항목 | 위치 | 이유 |
|------|------|------|
| **Firebase 설정** | `config.py` | 나중에 재사용 가능 (있어도 무해) |

---

## 🎯 Before vs After

### Before (Firebase 사용)
```python
# routers/musicgen_upload_router.py
from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
    firestore_service,  # ❌ 사용 안 함
)

# pyproject.toml
dependencies = [
    "firebase-admin>=6.5.0,<8.0.0",  # ❌ 불필요
]
```

**서버 로그:**
```
[firestore_service] WARNING: Firebase 자격증명/버킷이 누락되어 더미 모드로 전환합니다.
```

---

### After (MySQL 전용)
```python
# routers/musicgen_upload_router.py
from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
)

# MySQL 사용
from services.mysql_service import mysql_service

# pyproject.toml
dependencies = [
    "sqlalchemy>=2.0.0,<2.1.0",
    "pymysql>=1.1.0,<1.2.0",
    "cryptography>=41.0.0,<44.0.0",
]
```

**서버 로그:**
```
[MySQL] 연결 URL: mysql+pymysql://***@localhost:3307/readning
[MySQL] ✅ 데이터베이스 연결 성공
```

---

## 📊 데이터 저장 방식 비교

### Firebase Firestore (이전)
```
users/{uid}/books/{book_id}/
  └── chapters: [
        {
          page: 1,
          chunks: [...]
        }
      ]
```

### MySQL (현재)
```
books (책 정보)
  └── chapters (페이지)
      └── chunks (청크 + 음악 URL)
```

---

## 🔮 Firebase 재활성화 방법

나중에 Firebase가 필요하면 다음 단계로 복원:

### 1. 의존성 재추가
```bash
uv add firebase-admin
```

### 2. 서비스 파일 복원
```bash
move services\_deprecated\firestore_service.py services\firestore_service.py
```

### 3. Import 추가
```python
from services import firestore_service
```

### 4. Firebase 자격증명 설정
```bash
# .env 파일
FIREBASE_SA_PATH=./firebase-credentials.json
FIREBASE_BUCKET=readning.appspot.com
```

---

## 💡 왜 MySQL로 전환했나?

| 이유 | 설명 |
|------|------|
| **구조화된 데이터** | 책 → 챕터 → 청크 관계가 명확 |
| **복잡한 쿼리** | JOIN, 집계 등 자유로운 쿼리 |
| **로컬 개발** | Docker로 간편한 로컬 테스트 |
| **비용 효율** | RDS 프리티어 1년 무료 |
| **AWS 통합** | EC2 + RDS 통합 배포 용이 |

---

## ✅ 확인 사항

서버 재시작 후:
- [x] Firebase 경고 메시지 사라짐
- [x] MySQL 연결 성공 메시지 확인
- [x] 음악 생성 정상 작동
- [x] 동적 리더 정상 작동

---

**마이그레이션 완료일:** 2025-10-08  
**관련 이슈:** Firebase → MySQL 전환

