"""
감정 기반 리트리버 모듈

고급 검색 전략과 컨텍스트 재구성 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional, Callable
from utils.logger import log
from .vector_store import EmotionAwareVectorStore
from .emotion_chunker import EmotionChunk, create_overlapping_context


class EmotionAwareRetriever:
    """감정 인식 검색 엔진"""

    def __init__(self, vector_store: EmotionAwareVectorStore):
        """
        리트리버 초기화

        Args:
            vector_store: EmotionAwareVectorStore 인스턴스
        """
        self.vector_store = vector_store
        self.search_strategies = {
            "basic": self._basic_search,
            "emotion_boosted": self._emotion_boosted_search,
            "contextual": self._contextual_search,
            "hybrid": self._hybrid_search
        }

    def retrieve(
        self,
        query: str,
        k: int = 5,
        strategy: str = "emotion_boosted",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        검색 전략을 사용하여 관련 청크를 검색합니다.

        Args:
            query: 검색 쿼리
            k: 반환할 결과 개수
            strategy: 검색 전략 ("basic", "emotion_boosted", "contextual", "hybrid")
            **kwargs: 전략별 추가 파라미터

        Returns:
            검색 결과 리스트
        """
        if strategy not in self.search_strategies:
            log(f"⚠️ 알 수 없는 전략: {strategy}, 'basic'으로 폴백")
            strategy = "basic"

        log(f"🔍 검색 전략: {strategy}")
        search_func = self.search_strategies[strategy]
        return search_func(query, k, **kwargs)

    def _basic_search(self, query: str, k: int, **kwargs) -> List[Dict[str, Any]]:
        """기본 유사도 검색"""
        return self.vector_store.search(query, k=k)

    def _emotion_boosted_search(
        self,
        query: str,
        k: int,
        significance_boost: float = 0.1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """감정 전환점 중요도를 고려한 검색"""
        return self.vector_store.search_with_emotion_boost(
            query,
            k=k,
            significance_boost=significance_boost
        )

    def _contextual_search(
        self,
        query: str,
        k: int,
        context_window: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        앞뒤 문맥을 포함한 검색

        Args:
            context_window: 앞뒤로 포함할 청크 개수
        """
        # 기본 검색
        results = self.vector_store.search(query, k=k * 2)

        # 각 결과에 문맥 추가
        contextual_results = []
        for result in results:
            chunk_id = result["metadata"].get("chunk_id", 0)
            document_id = result["metadata"].get("document_id", "default")

            # 앞뒤 청크 가져오기
            context_chunks = []
            for offset in range(-context_window, context_window + 1):
                neighbor_id = f"{document_id}_chunk_{chunk_id + offset}"
                neighbor = self.vector_store.get_chunk_by_id(neighbor_id)
                if neighbor:
                    context_chunks.append(neighbor["document"])

            # 문맥 결합
            result["context"] = "\n\n".join(context_chunks) if context_chunks else result["document"]
            contextual_results.append(result)

        return contextual_results[:k]

    def _hybrid_search(
        self,
        query: str,
        k: int,
        emotion_weight: float = 0.3,
        context_window: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색: 유사도 + 감정 중요도 + 문맥

        Args:
            emotion_weight: 감정 중요도 가중치 (0-1)
            context_window: 문맥 윈도우 크기
        """
        # 1. 감정 부스트 검색
        results = self.vector_store.search_with_emotion_boost(query, k=k * 3)

        # 2. 문맥 추가
        hybrid_results = []
        for result in results:
            chunk_id = result["metadata"].get("chunk_id", 0)
            document_id = result["metadata"].get("document_id", "default")

            # 문맥 가져오기
            context_chunks = []
            for offset in range(-context_window, context_window + 1):
                neighbor_id = f"{document_id}_chunk_{chunk_id + offset}"
                neighbor = self.vector_store.get_chunk_by_id(neighbor_id)
                if neighbor:
                    context_chunks.append(neighbor["document"])

            result["context"] = "\n\n".join(context_chunks) if context_chunks else result["document"]

            # 3. 최종 스코어 계산
            base_score = result.get("boosted_distance", result.get("distance", 0))
            significance = result["metadata"].get("transition_significance", 0)

            # 하이브리드 스코어 (낮을수록 좋음)
            hybrid_score = base_score * (1 - emotion_weight) + (5 - significance) * emotion_weight
            result["hybrid_score"] = hybrid_score

            hybrid_results.append(result)

        # 최종 정렬
        hybrid_results.sort(key=lambda x: x["hybrid_score"])

        log(f"🎯 하이브리드 검색 완료: 상위 {k}개 반환")
        return hybrid_results[:k]

    def retrieve_by_emotion(
        self,
        query: str,
        emotion: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        특정 감정으로 필터링하여 검색

        Args:
            query: 검색 쿼리
            emotion: 필터링할 감정 (예: "슬픔", "기쁨")
            k: 반환할 결과 개수

        Returns:
            감정으로 필터링된 검색 결과
        """
        log(f"😊 감정 필터: '{emotion}'")
        return self.vector_store.search(query, k=k, emotion_filter=emotion)

    def retrieve_transitions(
        self,
        query: str,
        min_significance: int = 3,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        중요한 감정 전환점만 검색

        Args:
            query: 검색 쿼리
            min_significance: 최소 중요도 (1-5)
            k: 반환할 결과 개수

        Returns:
            중요한 전환점 검색 결과
        """
        log(f"🔄 전환점 검색: 중요도 >= {min_significance}")
        return self.vector_store.search(
            query,
            k=k,
            significance_threshold=min_significance
        )

    def format_results_for_llm(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool = True,
        use_context: bool = False
    ) -> str:
        """
        검색 결과를 LLM에 전달하기 좋은 형식으로 포맷팅

        Args:
            results: 검색 결과 리스트
            include_metadata: 메타데이터 포함 여부
            use_context: 문맥 사용 여부 (있는 경우)

        Returns:
            포맷팅된 텍스트
        """
        if not results:
            return "검색 결과가 없습니다."

        formatted_parts = []
        for i, result in enumerate(results, 1):
            text = result.get("context", result["document"]) if use_context else result["document"]

            part = f"[결과 {i}]\n{text}"

            if include_metadata and result.get("metadata"):
                meta = result["metadata"]
                metadata_str = f"\n[메타데이터: 감정={meta.get('emotion', 'N/A')}"

                if meta.get("transition_significance"):
                    metadata_str += f", 중요도={meta.get('transition_significance')}"

                if meta.get("next_emotion"):
                    metadata_str += f", 다음감정={meta.get('next_emotion')}"

                metadata_str += "]"
                part += metadata_str

            formatted_parts.append(part)

        return "\n\n---\n\n".join(formatted_parts)

    def get_emotional_arc(self, document_id: str = "default") -> List[Dict[str, Any]]:
        """
        문서의 감정 아크(흐름)를 추출합니다.

        Args:
            document_id: 문서 ID

        Returns:
            감정 전환점 타임라인
        """
        # 모든 청크를 위치 순으로 가져오기
        try:
            results = self.vector_store.collection.get(
                where={"document_id": document_id},
                limit=1000  # 충분히 큰 수
            )

            if not results["metadatas"]:
                return []

            # chunk_id로 정렬
            chunks_with_meta = [
                {
                    "chunk_id": meta.get("chunk_id", 0),
                    "emotion": meta.get("emotion", "unknown"),
                    "start_pos": meta.get("start_pos", 0),
                    "significance": meta.get("transition_significance"),
                    "next_emotion": meta.get("next_emotion"),
                    "explanation": meta.get("transition_explanation")
                }
                for meta in results["metadatas"]
            ]

            chunks_with_meta.sort(key=lambda x: x["chunk_id"])

            log(f"📈 감정 아크 추출: {len(chunks_with_meta)}개 청크")
            return chunks_with_meta

        except Exception as e:
            log(f"❌ 감정 아크 추출 실패: {e}")
            return []

    def explain_results(self, results: List[Dict[str, Any]]) -> str:
        """
        검색 결과에 대한 설명을 생성합니다.

        Args:
            results: 검색 결과

        Returns:
            설명 텍스트
        """
        if not results:
            return "검색 결과가 없습니다."

        explanation_parts = ["검색 결과 분석:\n"]

        # 감정 분포
        emotions = [r["metadata"].get("emotion", "unknown") for r in results]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        explanation_parts.append(f"감정 분포: {emotion_counts}")

        # 전환점 개수
        transitions = sum(1 for r in results if r["metadata"].get("is_transition_point"))
        explanation_parts.append(f"감정 전환점: {transitions}개")

        # 평균 중요도
        significances = [
            r["metadata"].get("transition_significance", 0)
            for r in results
            if r["metadata"].get("transition_significance")
        ]
        if significances:
            avg_sig = sum(significances) / len(significances)
            explanation_parts.append(f"평균 중요도: {avg_sig:.2f}/5")

        return "\n".join(explanation_parts)
