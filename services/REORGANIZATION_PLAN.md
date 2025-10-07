# 🗂️ Services 폴더 재구성 계획

## 현재 구조 (15개 파일)
```
services/
├── analyze_emotions_with_gpt.py
├── chunk_text_by_emotion.py
├── clean_json.py
├── ebooks2text.py
├── find_turning_points_in_text.py
├── firestore_service.py
├── get_emotion_analysis_prompt.py
├── merge_service.py
├── model_manager.py
├── musicgen_service.py
├── mysql_service.py
├── prompt_service.py
├── repeat_track.py
└── split_text.py
```

## 새로운 구조 (기능별 분류)

```
services/
│
├── text/                           # 📄 텍스트 처리
│   ├── __init__.py
│   ├── ebooks2text.py             # 전자책 → 텍스트 변환 (PDF, EPUB)
│   └── text_splitter.py           # 텍스트 분할 (split_text.py 개명)
│
├── emotion/                        # 🎭 감정 분석
│   ├── __init__.py
│   ├── analyzer.py                # GPT 감정 분석 (analyze_emotions_with_gpt.py 개명)
│   ├── turning_points.py          # 전환점 찾기 (find_turning_points_in_text.py 개명)
│   ├── chunk_by_emotion.py        # 감정 기반 청크 분할 (chunk_text_by_emotion.py)
│   └── prompts.py                 # 감정 분석 프롬프트 (get_emotion_analysis_prompt.py 개명)
│
├── music/                          # 🎵 음악 생성
│   ├── __init__.py
│   ├── generator.py               # MusicGen 음악 생성 (musicgen_service.py 개명)
│   ├── prompt_builder.py          # 음악 프롬프트 생성 (prompt_service.py 개명)
│   └── model_manager.py           # 모델 로딩/관리 (그대로 유지)
│
├── audio/                          # 🔊 오디오 처리
│   ├── __init__.py
│   ├── merger.py                  # 오디오 병합 (merge_service.py 개명)
│   └── repeater.py                # 오디오 반복 (repeat_track.py 개명)
│
├── database/                       # 💾 데이터베이스
│   ├── __init__.py
│   ├── mysql.py                   # MySQL 서비스 (mysql_service.py 개명)
│   └── firestore.py               # Firestore 서비스 (firestore_service.py 개명)
│
└── utils/                          # 🛠️ 공통 유틸리티
    ├── __init__.py
    └── json_cleaner.py            # JSON 정리 (clean_json.py 개명)
```

## 파일 이동 매핑

| 기존 파일 | → | 새 위치 |
|-----------|---|---------|
| `ebooks2text.py` | → | `text/ebooks2text.py` |
| `split_text.py` | → | `text/text_splitter.py` |
| `analyze_emotions_with_gpt.py` | → | `emotion/analyzer.py` |
| `find_turning_points_in_text.py` | → | `emotion/turning_points.py` |
| `chunk_text_by_emotion.py` | → | `emotion/chunk_by_emotion.py` |
| `get_emotion_analysis_prompt.py` | → | `emotion/prompts.py` |
| `musicgen_service.py` | → | `music/generator.py` |
| `prompt_service.py` | → | `music/prompt_builder.py` |
| `model_manager.py` | → | `music/model_manager.py` |
| `merge_service.py` | → | `audio/merger.py` |
| `repeat_track.py` | → | `audio/repeater.py` |
| `mysql_service.py` | → | `database/mysql.py` |
| `firestore_service.py` | → | `database/firestore.py` |
| `clean_json.py` | → | `utils/json_cleaner.py` |

## Import 경로 변경

### Before
```python
from services.musicgen_service import generate_music_samples
from services.chunk_text_by_emotion import chunk_text_by_emotion
from services.mysql_service import mysql_service
```

### After
```python
from services.music.generator import generate_music_samples
from services.emotion.chunk_by_emotion import chunk_text_by_emotion
from services.database.mysql import mysql_service
```

## 장점

✅ **명확한 책임 분리**: 각 폴더가 단일 책임을 가짐  
✅ **확장성**: 새 기능 추가 시 적절한 폴더에 배치  
✅ **가독성**: 파일 위치만으로도 역할 파악 가능  
✅ **유지보수**: 관련 파일들이 모여 있어 수정 용이  
✅ **테스트**: 각 카테고리별로 독립적인 테스트 가능

