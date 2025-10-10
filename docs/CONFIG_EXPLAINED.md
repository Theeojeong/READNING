# ⚙️ config.py 설정 값 설명

## 📊 설정 값 정리

### **OUTPUT_DIR**
```python
OUTPUT_DIR = "gen_musics"
```
**의미:** 생성된 음악 파일 저장 경로

**파일 구조:**
```
gen_musics/
└── {user_id}/
    └── {book_title}/
        └── page{N}/
            ├── chunk_1.wav
            ├── chunk_2.wav
            └── chunk_3.wav
```

---

### **GEN_DURATION**
```python
GEN_DURATION = 15  # 초 단위
```
**의미:** MusicGen이 각 청크마다 생성하는 음악 길이

**사용:**
```python
# services/model_manager.py
model.set_generation_params(duration=GEN_DURATION)  # 15초 음악 생성

# 생성 결과
chunk_1.wav → 15초
chunk_2.wav → 15초
chunk_3.wav → 15초
```

**주의:** 
- ✅ 초 단위 (15 = 15초)
- ❌ 밀리초 아님!

---

### **MAX_SEGMENT_SIZE**
```python
MAX_SEGMENT_SIZE = 6000  # 글자 수
```
**의미:** 자동 페이지 분할 시 각 페이지의 최대 글자 수

**동작:**
```
30,000자 텍스트
    ↓
자동 분할
├─ page 1: 0~6,000자
├─ page 2: 6,000~12,000자
├─ page 3: 12,000~18,000자
├─ page 4: 18,000~24,000자
└─ page 5: 24,000~30,000자
```

---

### **OVERLAP_SIZE**
```python
OVERLAP_SIZE = 600  # 글자 수
```
**의미:** 페이지 분할 시 겹침 영역

**목적:** 페이지 경계에서 맥락 유지

**동작:**
```
Page 1: [......... 600자 겹침]
Page 2: [600자 겹침 ......... 600자 겹침]
Page 3: [600자 겹침.........]
```

---

### **CHUNK_PREVIEW_LEN**
```python
CHUNK_PREVIEW_LEN = 300  # 글자 수
```
**의미:** 디버그 로그 출력 시 텍스트 미리보기 길이

---

## 🗑️ 제거된 레거시 설정

### **TOTAL_DURATION** (제거됨)
```python
# TOTAL_DURATION = 120  # ❌ 더 이상 사용 안 함
```
**원래 용도:** 병합된 음악 파일의 전체 길이  
**제거 이유:** 병합 기능 제거됨

**대체:** 라우터의 `target_len` 파라미터

---

### **FINAL_MIX_NAME** (제거됨)
```python
# FINAL_MIX_NAME = "final_mix.wav"  # ❌ 더 이상 사용 안 함
```
**원래 용도:** 병합된 파일명  
**제거 이유:** 개별 청크 파일로 변경 (`chunk_1.wav`, `chunk_2.wav`...)

---

## 🎯 설정 vs 라우터 파라미터

| 항목 | 타입 | 설명 | 변경 가능 |
|------|------|------|----------|
| **GEN_DURATION** | config | 각 청크 음악 길이 (고정) | 개발자만 |
| **target_len** | 파라미터 | 페이지 총 길이 (참고용) | 사용자 |
| **MAX_SEGMENT_SIZE** | config | 자동 페이지 분할 기준 | 개발자만 |

---

## 🔧 설정 수정 방법

### **개발자가 수정:**
```python
# config.py
GEN_DURATION = 30  # 15초 → 30초로 변경
MAX_SEGMENT_SIZE = 10000  # 6000자 → 10000자로 변경
```

### **사용자가 지정:**
```python
# API 요청 시
POST /generate/music-v3-long
{
    "target_len": 300  # 240초 → 300초로 변경
}
```

---

## 📊 실제 음악 길이 계산

```
실제 총 길이 = 청크 개수 × GEN_DURATION

예시:
- 청크 5개 × 15초 = 75초
- 청크 10개 × 15초 = 150초
- 청크 20개 × 15초 = 300초

target_len (240초)은 참고용일 뿐,
실제 길이는 위 공식으로 결정됨
```

---

## 💡 요약

| 설정 | 값 | 단위 | 용도 |
|------|-----|------|------|
| **GEN_DURATION** | 15 | 초 | 각 청크 음악 생성 길이 |
| **target_len** | 240 (기본) | 초 | 사용자 지정 참고값 |
| **MAX_SEGMENT_SIZE** | 6000 | 자 | 자동 페이지 분할 기준 |
| **OVERLAP_SIZE** | 600 | 자 | 페이지 겹침 영역 |

**제거된 것:**
- ❌ TOTAL_DURATION (레거시)
- ❌ FINAL_MIX_NAME (레거시)

