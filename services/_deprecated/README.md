# ⚠️ Deprecated Services

이 폴더의 파일들은 더 이상 사용되지 않습니다.

## 변경 사유

동적 Scrollama 리더에서는 각 청크별로 개별 음악 파일을 재생하므로,
음악을 하나의 파일로 병합하거나 반복 처리할 필요가 없어졌습니다.

### 변경 내역

- **2025-10-07**: 병합/반복 기능 제거
  - `merge_service.py` → deprecated
  - `repeat_track.py` → deprecated
  - `/generate/music-v3` API → deprecated (410 Gone)
  - `/generate/music-v3-long` API → 개별 청크 파일만 생성

## 대체 방안

### Before (병합 방식)
```python
# 모든 청크를 하나의 긴 파일로 병합
POST /generate/music-v3
→ ch1.wav (240초, 전체 병합)
```

### After (개별 청크 방식)
```python
# 각 청크별로 개별 파일 생성
POST /generate/music-v3-long
→ chunk_1.wav (30초)
→ chunk_2.wav (30초)
→ chunk_3.wav (30초)
...
```

## 삭제 예정

다음 메이저 버전에서 완전히 삭제될 예정입니다.

