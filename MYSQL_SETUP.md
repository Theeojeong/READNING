# 🗄️ MySQL 로컬 설정 가이드

Readning 프로젝트를 위한 MySQL 데이터베이스 설정 방법입니다.

## 📋 목차
1. [Docker를 이용한 설치 (추천)](#docker-설치)
2. [직접 설치](#직접-설치)
3. [데이터베이스 초기화](#데이터베이스-초기화)
4. [관리 도구](#관리-도구)
5. [문제 해결](#문제-해결)

---

## 🐳 Docker 설치 (추천)

### 1. Docker Compose로 실행 (가장 간단!)

```bash
# 프로젝트 루트에서 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f mysql

# 중지
docker-compose down

# 데이터 포함 완전 삭제
docker-compose down -v
```

### 2. 접속 확인

```bash
# MySQL 접속
docker exec -it readning-mysql mysql -u root -p
# 비밀번호: readning2024

# 또는 Python에서 테스트
python -c "from sqlalchemy import create_engine; \
            engine = create_engine('mysql+pymysql://readning_user:readning_pass@localhost:3306/readning'); \
            print('✅ 연결 성공!' if engine.connect() else '❌ 연결 실패')"
```

### 3. phpMyAdmin 접속 (웹 UI)

브라우저에서 http://localhost:8080 접속
- 서버: `mysql`
- 사용자: `root`
- 비밀번호: `readning2024`

---

## 💾 직접 설치

### Windows

1. [MySQL Community Server 다운로드](https://dev.mysql.com/downloads/mysql/)
2. MySQL Installer 실행
3. "Developer Default" 선택
4. Root 비밀번호 설정
5. 서비스 시작 확인

```powershell
# MySQL 서비스 시작
net start MySQL80

# MySQL 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE readning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### macOS

```bash
# Homebrew로 설치
brew install mysql

# 서비스 시작
brew services start mysql

# 초기 보안 설정
mysql_secure_installation
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install mysql-server

sudo systemctl start mysql
sudo systemctl enable mysql

sudo mysql_secure_installation
```

---

## 🔧 데이터베이스 초기화

### 방법 1: init-db.sql 직접 실행

```bash
# Docker 사용 시 (자동 실행됨)
docker exec -i readning-mysql mysql -u root -preadning2024 readning < init-db.sql

# 로컬 MySQL 사용 시
mysql -u root -p readning < init-db.sql
```

### 방법 2: Python 스크립트로 초기화

```python
# db_init.py
from services.mysql_service import engine
from init-db.sql 내용 복사하여 실행
```

---

## 🛠️ 관리 도구

### 1. MySQL Workbench (공식 GUI)
- [다운로드](https://dev.mysql.com/downloads/workbench/)
- 테이블 편집, 쿼리 실행, ER 다이어그램

### 2. phpMyAdmin (웹 기반)
- Docker Compose에 포함됨
- http://localhost:8080

### 3. DBeaver (무료, 다기능)
- [다운로드](https://dbeaver.io/download/)
- 여러 DB 지원, 데이터 시각화

### 4. VS Code Extension
- "MySQL" extension 설치
- VS Code에서 바로 쿼리 실행

---

## 🔍 유용한 쿼리

### 데이터 확인

```sql
-- 모든 책 조회
SELECT * FROM books;

-- 특정 챕터의 청크 조회
SELECT c.page, ch.chunk_index, ch.emotion, ch.text_preview
FROM chapters c
JOIN chunks ch ON c.id = ch.chapter_id
WHERE c.book_id = 'test_book_1'
ORDER BY c.page, ch.chunk_index;

-- 감정별 청크 통계
SELECT emotion, COUNT(*) as count
FROM chunks
GROUP BY emotion
ORDER BY count DESC;
```

### 백업 및 복원

```bash
# 백업
mysqldump -u root -p readning > backup.sql

# 복원
mysql -u root -p readning < backup.sql

# Docker 사용 시 백업
docker exec readning-mysql mysqldump -u root -preadning2024 readning > backup.sql
```

---

## 🆘 문제 해결

### 포트 3306이 이미 사용 중

```bash
# 다른 MySQL 프로세스 확인
netstat -ano | findstr :3306

# 해당 프로세스 종료
taskkill /PID [프로세스ID] /F

# 또는 Docker 포트 변경
docker run -p 3307:3306 ...
```

### 연결 거부 (Access denied)

```bash
# 비밀번호 재설정
docker exec -it readning-mysql mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### 한글 깨짐

```sql
-- 인코딩 확인
SHOW VARIABLES LIKE 'character%';

-- utf8mb4로 변경
ALTER DATABASE readning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🚀 Python 연동 확인

```python
# test_mysql.py
from sqlalchemy import create_engine, text
import os

DATABASE_URL = "mysql+pymysql://readning_user:readning_pass@localhost:3306/readning"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT DATABASE()"))
    print(f"✅ 연결된 데이터베이스: {result.fetchone()[0]}")
    
    result = conn.execute(text("SHOW TABLES"))
    print("📋 테이블 목록:")
    for row in result:
        print(f"  - {row[0]}")
```

---

## 📊 로컬 vs AWS 차이

| 항목 | 로컬 MySQL | AWS RDS |
|------|------------|---------|
| **연결 주소** | `localhost:3306` | `xxx.rds.amazonaws.com:3306` |
| **비용** | 무료 | 시간당 과금 |
| **백업** | 수동 | 자동 백업 |
| **확장성** | 제한적 | 쉽게 스펙업 |
| **보안** | 로컬 네트워크 | VPC, 보안그룹 |
| **개발 속도** | ⚡ 매우 빠름 | 네트워크 지연 |

**권장 사용법:**
- 개발: 로컬 Docker MySQL ✅
- 배포: AWS RDS ✅

---

## 🎯 다음 단계

1. ✅ MySQL 설치 및 실행
2. ✅ 데이터베이스 초기화
3. 📝 `services/mysql_service.py` 작성
4. 📝 `routers/musicgen_upload_router.py` 수정
5. 🧪 테스트 실행
6. 🚀 프론트엔드 연동

---

**문제가 있으신가요?** 
- Discord: [Readning 커뮤니티]
- GitHub Issues: [프로젝트 저장소]

