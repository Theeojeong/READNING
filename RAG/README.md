# 감정 기반 RAG 시스템

텍스트의 감정 전환점을 분석하여 의미론적으로 일관된 청크를 생성하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 주요 특징

### 1. 감정 기반 의미론적 청킹
- **고정 길이 청킹의 문제점 해결**: 문장/문단 중간에서 자르지 않음
- **감정 전환점 자동 감지**: LLM을 사용한 지능적인 경계 설정
- **문맥 보존**: 의미적으로 완결된 청크 생성

### 2. 고급 검색 전략
- **기본 유사도 검색**: 벡터 유사도 기반
- **감정 부스트 검색**: 감정 전환점 중요도 고려
- **문맥 포함 검색**: 앞뒤 청크를 포함한 확장 검색
- **하이브리드 검색**: 여러 전략을 결합한 최적화 검색

### 3. 메타데이터 활용
- 감정 정보 (예: "기쁨", "슬픔", "분노")
- 전환점 중요도 (1-5 등급)
- 위치 정보 및 청크 간 관계
- 감정 아크(흐름) 추적

## 설치

### 필수 패키지

```bash
pip install chromadb sentence-transformers pydantic
```

### 프로젝트 구조

```
RAG/
├── __init__.py              # 모듈 초기화
├── emotion_chunker.py       # 감정 기반 청킹 로직
├── vector_store.py          # 벡터 스토어 (ChromaDB)
├── retriever.py             # 고급 검색 기능
├── utils.py                 # 유틸리티 함수
├── example_usage.py         # 사용 예제
└── README.md                # 이 파일
```

## 빠른 시작

### 1. 기본 사용법

```python
from RAG import split_text_by_emotions, EmotionAwareVectorStore, EmotionAwareRetriever

# 텍스트 청킹
text = "여기에 긴 텍스트..."
chunks = split_text_by_emotions(text, max_chunk_size=2000)

# 벡터 스토어 초기화
vector_store = EmotionAwareVectorStore(collection_name="my_collection")
vector_store.add_chunks(chunks, document_id="doc_1")

# 검색
results = vector_store.search("검색 쿼리", k=5)
```

### 2. 고급 검색

```python
# 리트리버 초기화
retriever = EmotionAwareRetriever(vector_store)

# 감정 부스트 검색
results = retriever.retrieve(
    query="검색어",
    k=5,
    strategy="emotion_boosted"
)

# 하이브리드 검색
results = retriever.retrieve(
    query="검색어",
    k=5,
    strategy="hybrid",
    emotion_weight=0.3,
    context_window=1
)

# 특정 감정으로 필터링
results = retriever.retrieve_by_emotion(
    query="검색어",
    emotion="슬픔",
    k=5
)
```

### 3. 감정 아크 분석

```python
# 문서의 감정 흐름 추출
emotional_arc = retriever.get_emotional_arc(document_id="doc_1")

# 시각화
from RAG.utils import visualize_emotional_arc
print(visualize_emotional_arc(chunks))
```

## 상세 사용 예제

### 예제 1: 소설 텍스트 분석

```python
novel_text = """
행복한 하루였다. 친구들과 즐거운 시간을 보냈다.

그러나 갑자기 나쁜 소식을 들었다. 모든 것이 무너지는 것 같았다.

다행히 큰 문제는 아니었다. 안도의 한숨을 쉬었다.
"""

# 청킹
chunks = split_text_by_emotions(novel_text)

# 각 청크 확인
for chunk in chunks:
    print(f"감정: {chunk.emotion}")
    print(f"텍스트: {chunk.text}")
    print(f"전환점 여부: {chunk.metadata.get('is_transition_point')}")
    print()
```

### 예제 2: 파일에서 로드

```python
from RAG.utils import load_text_from_file, save_chunks_to_json

# 파일 로드
text = load_text_from_file("story.txt")

# 청킹
chunks = split_text_by_emotions(text, max_chunk_size=1500)

# JSON으로 저장
save_chunks_to_json(chunks, "chunks.json")
```

### 예제 3: 통계 분석

```python
from RAG.utils import get_emotion_statistics

# 통계 계산
stats = get_emotion_statistics(chunks)

print(f"총 청크 수: {stats['total_chunks']}")
print(f"평균 길이: {stats['avg_chunk_length']}")
print(f"감정 분포: {stats['emotion_distribution']}")
print(f"평균 중요도: {stats['avg_significance']}")
```

## API 레퍼런스

### EmotionChunk 클래스

```python
@dataclass
class EmotionChunk:
    text: str                          # 청크 텍스트
    emotion: str                       # 감정 ("기쁨", "슬픔" 등)
    start_pos: int                     # 시작 위치
    end_pos: int                       # 끝 위치
    chunk_id: int                      # 청크 ID
    metadata: Optional[Dict[str, Any]] # 추가 메타데이터
```

### split_text_by_emotions()

```python
def split_text_by_emotions(
    text: str,
    max_chunk_size: int = 2000,      # 최대 청크 크기
    min_chunk_size: int = 100,       # 최소 청크 크기
    overlap_size: int = 50           # 오버랩 크기
) -> List[EmotionChunk]
```

### EmotionAwareVectorStore

```python
# 초기화
vector_store = EmotionAwareVectorStore(
    collection_name="my_collection",
    persist_directory="./chroma_db",
    embedding_model="all-MiniLM-L6-v2"
)

# 청크 추가
vector_store.add_chunks(chunks, document_id="doc_1")

# 검색
results = vector_store.search(
    query="검색어",
    k=5,
    emotion_filter="슬픔",                    # 선택적
    significance_threshold=3                   # 선택적
)

# 감정 부스트 검색
results = vector_store.search_with_emotion_boost(
    query="검색어",
    k=5,
    significance_boost=0.1
)

# 통계
stats = vector_store.get_stats()
```

### EmotionAwareRetriever

```python
# 초기화
retriever = EmotionAwareRetriever(vector_store)

# 검색 전략
strategies = ["basic", "emotion_boosted", "contextual", "hybrid"]

results = retriever.retrieve(
    query="검색어",
    k=5,
    strategy="hybrid",
    emotion_weight=0.3,        # 하이브리드 전용
    context_window=1           # 문맥 관련 전용
)

# 감정별 검색
results = retriever.retrieve_by_emotion("검색어", emotion="기쁨", k=5)

# 중요 전환점만 검색
results = retriever.retrieve_transitions("검색어", min_significance=3, k=5)

# LLM용 포맷팅
formatted = retriever.format_results_for_llm(
    results,
    include_metadata=True,
    use_context=True
)
```

## 검색 전략 비교

| 전략 | 특징 | 사용 사례 |
|------|------|-----------|
| **basic** | 순수 벡터 유사도 | 빠른 검색, 감정 무관 |
| **emotion_boosted** | 전환점 중요도 가중치 | 극적인 변화 찾기 |
| **contextual** | 앞뒤 문맥 포함 | 긴 답변 생성 |
| **hybrid** | 모든 요소 결합 | 최고 품질 |

## 성능 최적화

### 1. 청킹 파라미터 조정

```python
# 짧은 텍스트
chunks = split_text_by_emotions(text, max_chunk_size=800)

# 긴 문서
chunks = split_text_by_emotions(text, max_chunk_size=3000)

# 정밀 분할
chunks = split_text_by_emotions(
    text,
    max_chunk_size=1500,
    min_chunk_size=200,
    overlap_size=100
)
```

### 2. 임베딩 모델 선택

```python
# 빠른 모델 (영어)
vector_store = EmotionAwareVectorStore(
    embedding_model="all-MiniLM-L6-v2"
)

# 다국어 모델
vector_store = EmotionAwareVectorStore(
    embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
)

# 고품질 모델
vector_store = EmotionAwareVectorStore(
    embedding_model="all-mpnet-base-v2"
)
```

### 3. 배치 처리

```python
# 여러 문서를 한 번에 처리
documents = [
    ("doc1", text1),
    ("doc2", text2),
    ("doc3", text3)
]

for doc_id, text in documents:
    chunks = split_text_by_emotions(text)
    vector_store.add_chunks(chunks, document_id=doc_id)
```

## 활용 사례

### 1. 소설/이야기 분석
- 감정 흐름 추적
- 클라이맥스 지점 찾기
- 캐릭터 감정 변화 분석

### 2. 고객 리뷰 분석
- 긍정/부정 전환점 감지
- 중요 불만 사항 추출
- 감정 기반 요약

### 3. 대화 시스템
- 문맥 인식 답변 생성
- 감정 공감 응답
- 적절한 톤 매칭

### 4. 문서 검색
- 의미론적 검색
- 관련 섹션 추출
- 문맥 기반 추천

## 문제 해결

### LLM 분석 실패 시

감정 분석이 실패하면 자동으로 문장 단위 폴백이 실행됩니다.

```python
# config.py에서 임계값 조정
SIGNIFICANCE_THRESHOLD = 3  # 낮추면 더 많은 전환점 포함
```

### 메모리 문제

```python
# 큰 텍스트는 분할 처리
def process_large_text(text, chunk_size=10000):
    for i in range(0, len(text), chunk_size):
        segment = text[i:i+chunk_size]
        chunks = split_text_by_emotions(segment)
        # 처리...
```

### ChromaDB 에러

```python
# 컬렉션 초기화
vector_store.clear_collection()

# 또는 완전히 새로 시작
import shutil
shutil.rmtree("./chroma_db")
```

## 기여 및 개선 아이디어

- [ ] 더 많은 임베딩 모델 지원
- [ ] 실시간 스트리밍 청킹
- [ ] GPU 가속 지원
- [ ] 다른 벡터 DB 연동 (Pinecone, Weaviate 등)
- [ ] 웹 인터페이스

## 라이선스

이 프로젝트는 기존 프로젝트의 일부입니다.

## 문의

문제가 있거나 개선 제안이 있으시면 이슈를 등록해주세요.
