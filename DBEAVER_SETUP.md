# 🐘 DBeaver로 MySQL 접속하기

## 📥 1. DBeaver 설치

### 다운로드
https://dbeaver.io/download/

**추천 버전:**
- Community Edition (무료)
- Windows / Mac / Linux 지원

---

## 🔌 2. MySQL 연결 설정

### Step 1: 새 연결 만들기

1. DBeaver 실행
2. **Database** → **New Database Connection** (또는 `Ctrl+Shift+N`)
3. **MySQL** 선택 → **Next**

---

### Step 2: 연결 정보 입력

```
┌─────────────────────────────────────────┐
│  Connection Settings                    │
├─────────────────────────────────────────┤
│  Host:        localhost                 │
│  Port:        3307  ← 중요! (3306 아님) │
│  Database:    readning                  │
│  Username:    readning_user             │
│  Password:    readning_pass             │
│                                         │
│  [ ] Show all databases                 │
│  [✓] Save password                      │
└─────────────────────────────────────────┘
```

**또는 root 계정:**
```
Username:    root
Password:    readning2024
```

---

### Step 3: 드라이버 다운로드

처음 연결 시:
```
Download driver files?
[Download]  ← 클릭
```

자동으로 MySQL JDBC 드라이버 다운로드됨

---

### Step 4: 테스트 및 연결

```
[Test Connection]  ← 클릭

✅ Connected
   
[Finish]  ← 클릭
```

---

## 📊 3. 데이터베이스 탐색

### 테이블 확인

```
Database Navigator (왼쪽 패널)
├─ readning
   ├─ Tables
   │  ├─ books             (책 정보)
   │  ├─ chapters          (페이지/챕터)
   │  ├─ chunks            (청크 + 음악)
   │  └─ user_preferences  (사용자 설정)
   ├─ Views
   └─ ...
```

### 데이터 보기

**방법 1: 더블 클릭**
- 테이블 더블 클릭 → 데이터 자동 표시

**방법 2: 컨텍스트 메뉴**
- 테이블 우클릭 → **View Data**

---

## 🔍 4. 유용한 쿼리

### SQL 에디터 열기

```
SQL Editor (상단 메뉴)
→ New SQL Editor (Ctrl+])
```

### 예제 쿼리

#### 모든 책 조회
```sql
SELECT * FROM books;
```

#### 특정 챕터의 청크 조회
```sql
SELECT 
    c.page,
    ch.chunk_index,
    ch.emotion,
    ch.text_preview,
    ch.audio_url
FROM chapters c
JOIN chunks ch ON c.id = ch.chapter_id
WHERE c.book_id = 'test_user_my_novel'
ORDER BY c.page, ch.chunk_index;
```

#### 감정별 청크 통계
```sql
SELECT 
    emotion,
    COUNT(*) as count
FROM chunks
GROUP BY emotion
ORDER BY count DESC;
```

#### 최근 생성된 책
```sql
SELECT 
    b.title,
    b.user_id,
    COUNT(DISTINCT c.page) as page_count,
    b.created_at
FROM books b
LEFT JOIN chapters c ON b.id = c.book_id
GROUP BY b.id
ORDER BY b.created_at DESC
LIMIT 10;
```

---

## ⚙️ 5. 고급 기능

### ER 다이어그램 생성

1. 데이터베이스 우클릭
2. **View Diagram** → **Entity Relationship**
3. 테이블 관계 시각화

```
books ─┬─ chapters ─┬─ chunks
       │            │
       └─ (1:N)     └─ (1:N)
```

---

### 데이터 내보내기

1. 테이블 우클릭 → **Export Data**
2. 포맷 선택:
   - CSV
   - JSON
   - SQL
   - Excel

---

### 데이터 가져오기

1. 테이블 우클릭 → **Import Data**
2. 파일 선택 (CSV, JSON 등)
3. 컬럼 매핑 확인
4. **Start Import**

---

## 🎨 6. 테마 및 설정

### 다크 모드
```
Window → Preferences → User Interface → Appearance
→ Theme: Dark
```

### 폰트 크기
```
Window → Preferences → User Interface → Fonts
→ Basic → Text Font
```

### 자동 완성
```
Window → Preferences → Editors → SQL Editor
→ [✓] Enable auto-completion
```

---

## 🆚 7. DBeaver vs phpMyAdmin

| 기능 | DBeaver | phpMyAdmin |
|------|---------|------------|
| **설치** | 별도 설치 필요 | 이미 설치됨 (Docker) |
| **UI** | 데스크톱 앱 | 웹 브라우저 |
| **성능** | 빠름 | 보통 |
| **기능** | 매우 많음 | 기본 기능 |
| **ER 다이어그램** | ✅ 자동 생성 | ❌ 없음 |
| **다중 DB 지원** | ✅ MySQL, PostgreSQL, MongoDB 등 | ❌ MySQL만 |
| **쿼리 자동완성** | ✅ 강력함 | ⚠️ 제한적 |
| **데이터 시각화** | ✅ 차트 생성 | ❌ 없음 |
| **추천** | 개발자, 복잡한 작업 | 빠른 확인, 간단한 작업 |

---

## 🚀 8. 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+Enter` | SQL 실행 |
| `Ctrl+]` | 새 SQL 에디터 |
| `Ctrl+Space` | 자동 완성 |
| `Ctrl+Shift+F` | SQL 포맷팅 |
| `F4` | 테이블 속성 보기 |
| `Ctrl+F7` | 다음 연결로 전환 |

---

## 🔧 9. 문제 해결

### "Connection Timeout"

**원인:** MySQL이 실행되지 않음

**해결:**
```bash
docker ps | grep mysql
# 또는
docker-compose up -d
```

---

### "Access denied for user"

**원인:** 비밀번호 오류

**해결:**
- 비밀번호 확인: `readning_pass` 또는 `readning2024`
- 사용자 확인: `readning_user` 또는 `root`

---

### "Unknown database 'readning'"

**원인:** 데이터베이스가 생성되지 않음

**해결:**
```bash
docker exec -it readning-mysql mysql -u root -preadning2024
CREATE DATABASE readning;
# 또는
docker-compose restart mysql
```

---

## 💡 10. 추천 플러그인

### SQL Formatter
```
Help → Install New Software
→ Search: "SQL Formatter"
```

### Git Integration
```
Help → Install New Software
→ Search: "EGit"
```

---

## 📚 11. 참고 자료

- [DBeaver 공식 문서](https://dbeaver.com/docs/)
- [DBeaver GitHub](https://github.com/dbeaver/dbeaver)
- [MySQL 8.0 문서](https://dev.mysql.com/doc/refman/8.0/en/)

---

## 🎯 빠른 시작 체크리스트

- [ ] DBeaver 다운로드 및 설치
- [ ] MySQL 연결 설정 (localhost:3307)
- [ ] 드라이버 다운로드
- [ ] 연결 테스트
- [ ] readning 데이터베이스 확인
- [ ] 테이블 데이터 조회
- [ ] SQL 쿼리 실행
- [ ] ER 다이어그램 생성

---

**현재 연결 정보 요약:**
```
Host:     localhost
Port:     3307  ← 주의!
Database: readning
User:     readning_user
Password: readning_pass
```

DBeaver로 강력한 데이터베이스 관리를 시작하세요! 🐘✨

