"""
감정 기반 벡터 스토어 모듈

청크를 임베딩하고 벡터 데이터베이스에 저장/검색합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from utils.logger import log
from .emotion_chunker import EmotionChunk


class EmotionAwareVectorStore:
    """감정 메타데이터를 포함한 벡터 스토어"""

    def __init__(
        self,
        collection_name: str = "emotion_chunks",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        벡터 스토어 초기화

        Args:
            collection_name: 컬렉션 이름
            persist_directory: 데이터 저장 디렉토리
            embedding_model: 임베딩 모델 (sentence-transformers 모델명)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Chroma DB 클라이언트 초기화
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 임베딩 함수 설정
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )

        # 컬렉션 생성 또는 가져오기
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            log(f"📚 기존 컬렉션 로드: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Emotion-aware text chunks"}
            )
            log(f"✨ 새 컬렉션 생성: {collection_name}")

    def add_chunks(self, chunks: List[EmotionChunk], document_id: str = "default") -> None:
        """
        청크를 벡터 스토어에 추가합니다.

        Args:
            chunks: EmotionChunk 객체 리스트
            document_id: 문서 식별자
        """
        if not chunks:
            log("⚠️ 추가할 청크가 없습니다")
            return

        log(f"💾 벡터 스토어에 {len(chunks)}개 청크 추가 중...")

        # 데이터 준비
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_full_id = f"{document_id}_chunk_{chunk.chunk_id}"
            ids.append(chunk_full_id)
            documents.append(chunk.text)

            # 메타데이터 준비
            metadata = {
                "document_id": document_id,
                "chunk_id": chunk.chunk_id,
                "emotion": chunk.emotion,
                "start_pos": chunk.start_pos,
                "end_pos": chunk.end_pos,
                "text_length": len(chunk.text),
            }

            # 추가 메타데이터 병합
            if chunk.metadata:
                for key, value in chunk.metadata.items():
                    # Chroma는 기본 타입만 지원하므로 변환
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
                    else:
                        metadata[key] = str(value)

            metadatas.append(metadata)

        # 벡터 스토어에 추가
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            log(f"✅ {len(chunks)}개 청크 추가 완료")
        except Exception as e:
            log(f"❌ 청크 추가 실패: {e}")
            raise

    def search(
        self,
        query: str,
        k: int = 5,
        emotion_filter: Optional[str] = None,
        significance_threshold: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            k: 반환할 결과 개수
            emotion_filter: 특정 감정으로 필터링 (예: "슬픔")
            significance_threshold: 최소 중요도 (1-5)

        Returns:
            검색 결과 리스트 [{"document": str, "metadata": dict, "distance": float}]
        """
        log(f"🔍 검색 쿼리: '{query[:50]}...' (k={k})")

        # 필터 조건 생성
        where_filter = {}
        if emotion_filter:
            where_filter["emotion"] = emotion_filter
        if significance_threshold:
            where_filter["transition_significance"] = {"$gte": significance_threshold}

        try:
            # 검색 실행
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter if where_filter else None
            )

            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                        "id": results["ids"][0][i] if results["ids"] else ""
                    })

            log(f"✅ 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results

        except Exception as e:
            log(f"❌ 검색 실패: {e}")
            return []

    def search_with_emotion_boost(
        self,
        query: str,
        k: int = 5,
        significance_boost: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        감정 전환점 중요도를 고려한 검색 (재랭킹)

        Args:
            query: 검색 쿼리
            k: 최종 반환할 결과 개수
            significance_boost: 중요도당 부스트 비율 (예: 0.1 = 10%)

        Returns:
            재랭킹된 검색 결과
        """
        # 더 많이 검색 (재랭킹 위해)
        results = self.search(query, k=k * 2)

        # 중요도 기반 재랭킹
        for result in results:
            significance = result["metadata"].get("transition_significance", 0)
            original_distance = result["distance"]

            # 중요도가 높을수록 거리를 줄임 (유사도 증가)
            boosted_distance = original_distance * (1 - significance * significance_boost)
            result["original_distance"] = original_distance
            result["boosted_distance"] = boosted_distance

        # 재정렬
        results.sort(key=lambda x: x["boosted_distance"])

        log(f"🎯 재랭킹 완료: 상위 {k}개 반환")
        return results[:k]

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 청크를 가져옵니다.

        Args:
            chunk_id: 청크 ID

        Returns:
            청크 데이터 또는 None
        """
        try:
            result = self.collection.get(ids=[chunk_id])
            if result["documents"]:
                return {
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                    "id": chunk_id
                }
        except Exception as e:
            log(f"❌ 청크 조회 실패: {e}")

        return None

    def delete_document(self, document_id: str) -> None:
        """
        특정 문서의 모든 청크를 삭제합니다.

        Args:
            document_id: 문서 ID
        """
        try:
            # document_id로 필터링하여 삭제
            self.collection.delete(where={"document_id": document_id})
            log(f"🗑️ 문서 삭제 완료: {document_id}")
        except Exception as e:
            log(f"❌ 문서 삭제 실패: {e}")

    def clear_collection(self) -> None:
        """컬렉션의 모든 데이터를 삭제합니다."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            log(f"🗑️ 컬렉션 초기화 완료: {self.collection_name}")
        except Exception as e:
            log(f"❌ 컬렉션 초기화 실패: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        벡터 스토어 통계를 반환합니다.

        Returns:
            통계 정보 딕셔너리
        """
        try:
            count = self.collection.count()

            # 감정별 분포 계산 (샘플링)
            sample_size = min(100, count)
            if sample_size > 0:
                sample = self.collection.get(limit=sample_size)
                emotions = [meta.get("emotion", "unknown") for meta in sample["metadatas"]]
                emotion_counts = {}
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

                return {
                    "total_chunks": count,
                    "collection_name": self.collection_name,
                    "emotion_distribution": emotion_counts,
                    "sample_size": sample_size
                }

            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }

        except Exception as e:
            log(f"❌ 통계 조회 실패: {e}")
            return {"error": str(e)}
