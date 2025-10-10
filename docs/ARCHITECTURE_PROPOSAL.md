# 🏗️ Readning 아키텍처 개선 제안

## 현재 아키텍처 평가

### ✅ 강점
1. **2단계 청크 분할**: LLM 한계와 의미적 일관성 모두 고려
2. **감정 기반 분할**: 내러티브 흐름에 맞는 음악 생성
3. **캐싱 전략**: MySQL 기반 효율적 재사용
4. **자동 페이지 분할**: 사용자 편의성

### ⚠️ 개선 필요 영역
1. LLM API 호출 비용
2. 페이지 경계에서 감정 전환점 손실
3. 처리 시간
4. 감정 분석 정확도

---

## 🎯 개선 방안

### 방안 1: 슬라이딩 윈도우 (Sliding Window)

```python
def split_with_overlap(text, max_size=6000, overlap=600):
    """
    페이지 경계에 오버랩 추가하여 전환점 보존
    """
    pages = []
    start = 0
    
    while start < len(text):
        # 기본 페이지
        end = min(start + max_size, len(text))
        
        # 다음 페이지와 겹치는 부분 포함
        if end < len(text):
            overlap_end = min(end + overlap, len(text))
            page_text = text[start:overlap_end]
        else:
            page_text = text[start:end]
            
        pages.append({
            'text': page_text,
            'start': start,
            'end': end,
            'has_overlap': end < len(text)
        })
        
        start = end  # overlap 제외하고 다음 시작
    
    return pages
```

**장점:**
- 페이지 경계에서 감정 전환점 포착
- 연속성 보장
- 자연스러운 음악 전환

---

### 방안 2: 계층적 분석 (Hierarchical Analysis)

```python
class HierarchicalAnalyzer:
    """
    전체 → 장(chapter) → 절(section) → 청크 순으로 분석
    """
    
    def analyze(self, text):
        # 1단계: 전체 요약 (1회 호출)
        global_summary = self.get_global_summary(text[:2000])
        
        # 2단계: 장 단위 분석 (주요 전환점만)
        chapters = self.detect_chapters(text)
        
        # 3단계: 각 장 내에서 세부 청크
        chunks = []
        for chapter in chapters:
            chapter_chunks = self.analyze_chapter(
                chapter.text,
                global_context=global_summary
            )
            chunks.extend(chapter_chunks)
        
        return chunks
    
    def detect_chapters(self, text):
        """
        휴리스틱 기반 장 구분
        - 빈 줄 2개 이상
        - "제1장", "Chapter 1" 등 패턴
        - 시간/장소 전환 표현
        """
        # 구현...
```

**장점:**
- LLM 호출 최적화 (30-50% 감소)
- 전체 맥락 파악 후 세부 분석
- 더 정확한 감정 흐름 파악

---

### 방안 3: 하이브리드 접근 (Hybrid Approach)

```python
class HybridChunker:
    """
    규칙 기반 + AI 기반 혼합
    """
    
    def process(self, text):
        # 1. 규칙 기반 1차 분할
        rule_based_chunks = self.rule_based_split(text)
        
        # 2. 중요 부분만 LLM 분석
        critical_chunks = []
        for chunk in rule_based_chunks:
            if self.is_critical(chunk):  # 대화, 갈등, 전환 등
                # LLM으로 정밀 분석
                refined = self.llm_analyze(chunk)
                critical_chunks.append(refined)
            else:
                # 규칙 기반 유지
                critical_chunks.append(chunk)
        
        return critical_chunks
    
    def rule_based_split(self, text):
        """
        문단, 대화, 장면 전환 등 패턴 인식
        """
        patterns = [
            r'\n\n+',  # 문단
            r'".+"',   # 대화
            r'[.!?]',  # 문장
        ]
        # 구현...
    
    def is_critical(self, chunk):
        """
        LLM 분석이 필요한 중요 부분 판단
        """
        indicators = [
            '대화 많음',
            '감정 표현',
            '갈등 상황',
            '장면 전환'
        ]
        # 구현...
```

**장점:**
- 비용 70% 절감
- 처리 속도 2배 향상
- 중요 부분은 정밀 분석

---

### 방안 4: 스트리밍 처리 (Streaming Processing)

```python
async def stream_process(file_path):
    """
    전체 로드 대신 스트리밍으로 점진적 처리
    """
    async with aiofiles.open(file_path, 'r') as f:
        buffer = ""
        processed_chunks = []
        
        async for line in f:
            buffer += line
            
            # 버퍼가 충분히 차면 처리
            if len(buffer) >= 6000:
                # 문장 경계 찾기
                last_sentence = buffer.rfind('.')
                if last_sentence > 4000:
                    # 처리할 청크
                    chunk = buffer[:last_sentence+1]
                    buffer = buffer[last_sentence+1:]
                    
                    # 비동기 처리
                    result = await process_chunk(chunk)
                    processed_chunks.append(result)
                    
                    # 즉시 저장 (점진적)
                    await save_to_db(result)
        
        # 남은 버퍼 처리
        if buffer:
            result = await process_chunk(buffer)
            processed_chunks.append(result)
    
    return processed_chunks
```

**장점:**
- 메모리 효율적 (대용량 파일 가능)
- 점진적 결과 제공
- 사용자가 첫 페이지 빠르게 확인

---

## 📊 비교 분석

| 방안 | LLM 비용 | 처리 시간 | 정확도 | 구현 복잡도 |
|------|---------|-----------|--------|------------|
| **현재** | 높음 | 보통 | 높음 | 낮음 |
| **슬라이딩 윈도우** | 높음 | 보통 | 매우 높음 | 보통 |
| **계층적 분석** | 보통 | 빠름 | 높음 | 높음 |
| **하이브리드** | 낮음 | 빠름 | 보통 | 높음 |
| **스트리밍** | 높음 | 빠름* | 높음 | 보통 |

*첫 결과까지의 시간

---

## 🎯 권장 사항

### 단기 개선 (Quick Win)
1. **슬라이딩 윈도우** 적용
   - 현재 코드에 쉽게 통합 가능
   - 즉시 품질 향상

2. **캐싱 강화**
   ```python
   # 감정 분석 결과도 캐싱
   emotion_cache[text_hash] = analysis_result
   ```

### 중기 개선
1. **하이브리드 접근** 도입
   - 비용 대폭 절감
   - 성능 유지

2. **배치 처리**
   ```python
   # 여러 청크를 한 번에 LLM에 전송
   batch_analyze(chunks[:5])  # 5개씩 묶어서
   ```

### 장기 개선
1. **자체 감정 분석 모델**
   - 로컬 BERT 모델 fine-tuning
   - API 비용 제로

2. **사용자 피드백 학습**
   - 청크 분할 품질 개선
   - 음악 매칭 정확도 향상

---

## 💡 추가 아이디어

### 1. 프리셋 템플릿
```python
GENRE_TEMPLATES = {
    'romance': {
        'chunk_size': 4000,  # 짧게
        'emotion_weight': 0.8,  # 감정 중심
        'music_style': 'melodic'
    },
    'thriller': {
        'chunk_size': 8000,  # 길게
        'emotion_weight': 0.3,  # 긴장감 중심
        'music_style': 'dramatic'
    }
}
```

### 2. 적응형 청킹
```python
def adaptive_chunking(text, user_feedback):
    """
    사용자 피드백으로 청크 크기 자동 조절
    """
    if user_feedback.avg_skip_rate > 0.3:
        # 자주 스킵하면 청크 크기 감소
        chunk_size *= 0.8
    # ...
```

### 3. 병렬 파이프라인
```python
async def parallel_pipeline(text):
    """
    분석과 음악 생성을 병렬로
    """
    tasks = []
    for page in pages:
        # 분석과 생성을 동시에
        tasks.append(analyze_and_generate(page))
    
    results = await asyncio.gather(*tasks)
    return results
```

---

## 🏆 결론

현재 아키텍처는 **매우 우수**합니다:
- ✅ 2단계 분할 전략
- ✅ 감정 기반 음악 생성
- ✅ 자동화 및 캐싱

**권장 개선:**
1. 즉시: 슬라이딩 윈도우 (품질 향상)
2. 다음: 하이브리드 접근 (비용 절감)
3. 미래: 자체 모델 (완전 자립)

"**Good architecture, but can be GREAT!**" 🚀
