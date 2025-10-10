# 📄 page 파라미터 완벽 가이드

`page`가 무엇이고, 언제 필요한지 명확하게 설명합니다.

---

## 🤔 page가 뭔가요?

### **간단히:**
> **"같은 책(book_title)을 여러 번 나눠서 업로드할 때 구분하는 번호"**

---

## 📊 실제 예시

### **예시 1: 짧은 소설 (page 불필요)**

```
📖 "운수 좋은 날" (1만 자)
   ↓
[전체를 한 파일로 업로드]
   ↓
POST /generate/music-v3-long
- file: "운수좋은날_전체.txt"
- book_title: "운수좋은날"
- page: 1  ← 전체가 page 1

결과:
└─ page 1 → 전체 내용 → chunks 2개
```

---

### **예시 2: 긴 소설 (page 필요)**

```
📖 "해리포터" (10만 자)
   ↓
[너무 길어서 3개 파일로 나눔]
   ↓
1차: POST /generate/music-v3-long
- file: "해리포터_1-5장.txt"  (3만 자)
- book_title: "해리포터"
- page: 1  ← 1부

2차: POST /generate/music-v3-long
- file: "해리포터_6-10장.txt"  (3만 자)
- book_title: "해리포터"  
- page: 2  ← 2부

3차: POST /generate/music-v3-long
- file: "해리포터_11-15장.txt"  (4만 자)
- book_title: "해리포터"
- page: 3  ← 3부

결과:
├─ page 1 → 1-5장 → chunks 15개
├─ page 2 → 6-10장 → chunks 12개
└─ page 3 → 11-15장 → chunks 18개
```

---

## 🗄️ MySQL에 저장되는 방식

```sql
-- chapters 테이블
book_id: "alice_해리포터"
├─ page: 1, total_duration: 240
├─ page: 2, total_duration: 240
└─ page: 3, total_duration: 240

-- chunks 테이블
chapter_id=1 (page 1)
├─ chunk 1, 2, 3... (1-5장의 청크들)

chapter_id=2 (page 2)
├─ chunk 1, 2, 3... (6-10장의 청크들)

chapter_id=3 (page 3)
├─ chunk 1, 2, 3... (11-15장의 청크들)
```

---

## 🎯 언제 사용하나요?

### ✅ **page를 변경해야 하는 경우:**

1. **긴 책을 여러 파일로 나눠서 업로드**
   ```
   file1.txt → page=1
   file2.txt → page=2
   file3.txt → page=3
   ```

2. **책을 부분적으로 재생성**
   ```
   page=2만 다시 생성하고 싶을 때
   → page=2로 재업로드
   ```

3. **여러 챕터를 따로 관리**
   ```
   1부 → page=1
   2부 → page=2
   에필로그 → page=99
   ```

---

### ❌ **page를 변경하지 않아도 되는 경우 (대부분):**

1. **짧은/중간 길이 텍스트**
   ```
   5,000자 소설 → page=1만 사용
   ```

2. **한 파일에 전체 내용**
   ```
   전체.txt → page=1로 충분
   ```

3. **일반적인 사용**
   ```
   대부분 page=1만 사용
   ```

---

## 🆕 자동 페이지 분할 API (NEW!)

page 입력이 귀찮다면 자동 분할 API를 사용하세요:

### **`POST /generate/music-auto`**

```python
# page 파라미터 없음!
POST /generate/music-auto
{
    "file": "긴소설.txt",  (50,000자)
    "user_id": "alice",
    "book_title": "긴소설",
    # page 없음!
}

자동 처리:
→ 50,000자를 6,000자 단위로 자동 분할
→ page 1, 2, 3, ..., 9 자동 생성
→ 각 페이지별 음악 생성
→ MySQL 자동 저장

응답:
{
    "total_pages": 9,
    "pages": [
        {"page": 1, "chunks": 5},
        {"page": 2, "chunks": 4},
        ...
        {"page": 9, "chunks": 3}
    ]
}
```

---

## 📋 API 선택 가이드

### **어떤 API를 사용해야 하나요?**

| 상황 | 추천 API | 이유 |
|------|---------|------|
| 짧은 텍스트 (<10,000자) | `/music-v3-long` (page=1) | 빠르고 간단 |
| 긴 텍스트 (>20,000자) | `/music-auto` ✨ | 자동 분할, 안전 |
| 여러 파일 나눠서 업로드 | `/music-v3-long` (page 변경) | 수동 제어 |
| 귀찮다! 자동으로! | `/music-auto` ✨ | page 입력 불필요 |

---

## 🎬 웹에서 보는 방법

### **page가 여러 개인 경우:**

```javascript
// page 1 보기
http://localhost:8000/scrollama/dynamic-reader.html?user_id=alice&book_title=해리포터&page=1

// page 2 보기
http://localhost:8000/scrollama/dynamic-reader.html?user_id=alice&book_title=해리포터&page=2

// page 3 보기
http://localhost:8000/scrollama/dynamic-reader.html?user_id=alice&book_title=해리포터&page=3
```

**페이지 네비게이션:**
- "< 이전 페이지" 버튼 → `page=1`
- "다음 페이지 >" 버튼 → `page=2`

---

## 💡 결론

### **page 파라미터의 역할:**

```
page = "이 파일이 책의 몇 번째 부분인지"

비유:
- 책을 3권으로 나눠 출판한다면
  → 1권, 2권, 3권
  → page=1, page=2, page=3

- 드라마를 시즌으로 나눈다면
  → 시즌 1, 시즌 2, 시즌 3
  → page=1, page=2, page=3
```

### **대부분의 경우:**
- ✅ **page=1만 사용** (파일 하나 = 전체)
- ✅ 필요하면 변경
- ✅ 또는 `/music-auto` 사용 (완전 자동)

---

## 🚀 다음 단계

main.py에 새 라우터를 추가했으니 서버를 재시작하면:

```
http://localhost:8000/docs

새로운 엔드포인트:
✨ POST /generate/music-auto  (자동 페이지 분할)
```

이제 명확해지셨나요? 😊

**요약:**
- `page` = 같은 책의 "몇 번째 파트"인지 구분하는 번호
- 대부분 1만 사용
- 자동 분할 원하면 `/music-auto` 사용!
