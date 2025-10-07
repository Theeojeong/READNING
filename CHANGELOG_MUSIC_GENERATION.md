# 🎵 음악 생성 아키텍처 변경 로그

## 2025-10-07: 병합/반복 처리 제거

### 📋 변경 사유

동적 Scrollama 리더에서는 사용자가 스크롤할 때마다 해당 청크의 음악이 자동으로 재생됩니다.
따라서 모든 청크를 하나의 긴 파일로 병합할 필요가 없어졌습니다.

### ✅ 변경 사항

#### 1. API 변경

**Deprecated:**
- `POST /generate/music-v3` → 410 Gone (더 이상 지원 안 함)
  - 병합된 단일 파일 생성 방식

**Active:**
- `POST /generate/music-v3-long` → 개별 청크 파일 생성
  - 각 청크별로 독립적인 음악 파일 생성
  - MySQL에 메타데이터 저장

#### 2. 코드 변경

**삭제된 코드:**
- `routers/musicgen_upload_router.py`:
  - 병합/반복 처리 코드 제거 (라인 173-195)
  - `get_output_path()` 함수 제거
  - 파일 존재 체크 → MySQL 기반으로 변경
  - import 정리 (`merge_service`, `repeat_track` 제거)

**Deprecated 파일:**
- `services/_deprecated/merge_service.py` (이동)
- `services/_deprecated/repeat_track.py` (이동)

#### 3. API 응답 변경

**Before:**
```json
{
  "message": "my_novel p1 음원 생성 완료",
  "download_url": "/gen_musics/user123/my_novel/ch1.wav",
  "page": 1
}
```

**After:**
```json
{
  "message": "my_novel p1 음원 생성 완료",
  "page": 1,
  "chunks": 5,
  "book_id": "user123_my_novel",
  "audio_files": [
    "/gen_musics/user123/my_novel/chunk_1.wav",
    "/gen_musics/user123/my_novel/chunk_2.wav",
    "/gen_musics/user123/my_novel/chunk_3.wav",
    "/gen_musics/user123/my_novel/chunk_4.wav",
    "/gen_musics/user123/my_novel/chunk_5.wav"
  ]
}
```

**캐시된 경우:**
```json
{
  "message": "my_novel p1 이미 생성됨 (캐시 사용)",
  "page": 1,
  "chunks": 5,
  "book_id": "user123_my_novel",
  "cached": true
}
```

### 🎯 장점

#### 1. 성능 향상
- ✅ 병합 처리 시간 제거 (약 10-30초 단축)
- ✅ 메모리 사용량 감소
- ✅ 디스크 I/O 감소

#### 2. 사용자 경험 개선
- ✅ 각 청크별로 정확한 음악 매칭
- ✅ 스크롤 시 즉시 음악 전환
- ✅ 감정 흐름에 따른 자연스러운 음악 변화

#### 3. 개발 유지보수
- ✅ 코드 복잡도 감소
- ✅ 에러 포인트 감소
- ✅ 명확한 책임 분리

#### 4. 확장성
- ✅ 청크별 독립적인 캐싱 가능
- ✅ 다양한 재생 방식 지원 가능
- ✅ A/B 테스트 용이

### 📊 파일 구조 변경

**Before:**
```
gen_musics/
└── user123/
    └── my_novel/
        └── ch1.wav (240초, 전체 병합)
```

**After:**
```
gen_musics/
└── user123/
    └── my_novel/
        ├── chunk_1.wav (30초)
        ├── chunk_2.wav (30초)
        ├── chunk_3.wav (30초)
        ├── chunk_4.wav (30초)
        └── chunk_5.wav (30초)
```

### 🔄 마이그레이션 가이드

#### 기존 코드 업데이트

**Before:**
```python
# 병합된 파일 다운로드
response = requests.post('/generate/music-v3', files=files, data=data)
audio_url = response.json()['download_url']
```

**After:**
```python
# 개별 청크 파일 생성
response = requests.post('/generate/music-v3-long', files=files, data=data)
book_id = response.json()['book_id']
page = response.json()['page']

# 리더 페이지로 이동
url = f"/reader?user_id={user_id}&book_title={book_title}&page={page}"
```

#### 프론트엔드 연동

```javascript
// API 호출
const response = await fetch('/generate/music-v3-long', {
  method: 'POST',
  body: formData
});

const data = await response.json();

// 동적 리더 페이지로 리다이렉트
window.location.href = `/reader?user_id=${userId}&book_title=${bookTitle}&page=${data.page}`;
```

### 🧪 테스트

```python
# 테스트 코드 예시
def test_music_generation_individual_chunks():
    response = client.post(
        "/generate/music-v3-long",
        files={"file": open("test.txt", "rb")},
        data={
            "user_id": "test_user",
            "book_title": "test_book",
            "page": 1,
            "target_len": 240
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert "audio_files" in data
    assert len(data["audio_files"]) > 0
    
    # 각 청크 파일이 실제로 생성되었는지 확인
    for audio_url in data["audio_files"]:
        file_path = audio_url.lstrip('/')
        assert os.path.exists(file_path)
```

### 📝 주의사항

1. **기존 병합 파일과 호환성 없음**
   - 새 API는 개별 청크 파일만 생성
   - 기존 `ch1.wav` 형식 파일은 생성되지 않음

2. **캐싱 확인**
   - MySQL에 이미 데이터가 있으면 음악 재생성을 건너뜀
   - 강제 재생성이 필요하면 DB에서 삭제 후 재실행

3. **Deprecated API**
   - `/generate/music-v3` 호출 시 410 Gone 에러 발생
   - 프론트엔드 코드를 `/generate/music-v3-long`으로 변경 필요

### 🚀 다음 단계

- [ ] 프론트엔드 API 엔드포인트 업데이트
- [ ] 기존 병합 파일 정리 (선택사항)
- [ ] 청크별 캐싱 전략 구현
- [ ] 청크 파일 압축 (용량 최적화)
- [ ] S3 업로드 자동화

---

**참고 문서:**
- [QUICKSTART.md](QUICKSTART.md) - 빠른 시작 가이드
- [MYSQL_SETUP.md](MYSQL_SETUP.md) - MySQL 설정 가이드
- [services/_deprecated/README.md](services/_deprecated/README.md) - Deprecated 파일 설명

