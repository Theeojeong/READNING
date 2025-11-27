"""
RAG 시스템 사용 예제

감정 기반 청킹과 검색을 사용하는 방법을 보여줍니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from RAG.emotion_chunker import split_text_by_emotions
from RAG.vector_store import EmotionAwareVectorStore
from RAG.retriever import EmotionAwareRetriever
from RAG.utils import (
    load_text_from_file,
    save_chunks_to_json,
    get_emotion_statistics,
    visualize_emotional_arc
)


def example_basic_chunking():
    """기본 청킹 예제"""
    print("\n" + "=" * 60)
    print("예제 1: 기본 감정 기반 청킹")
    print("=" * 60)

    # 샘플 텍스트
    sample_text = """
    오늘은 정말 행복한 하루였다. 친구들과 즐거운 시간을 보냈고,
    맛있는 음식도 먹었다. 모든 것이 완벽했다.

    그러나 집에 돌아오는 길에 나쁜 소식을 들었다.
    할머니께서 편찮으시다는 전화를 받았다.
    순간 세상이 무너지는 것 같았다.

    병원으로 달려갔다. 다행히 큰 문제는 아니었다.
    안도의 한숨을 쉬었다. 가족이 얼마나 소중한지 다시 깨달았다.
    """

    # 청킹 실행
    chunks = split_text_by_emotions(
        sample_text,
        max_chunk_size=200,
        min_chunk_size=50
    )

    # 결과 출력
    print(f"\n총 {len(chunks)}개의 청크 생성됨\n")

    for i, chunk in enumerate(chunks):
        print(f"청크 {i + 1}:")
        print(f"  감정: {chunk.emotion}")
        print(f"  위치: {chunk.start_pos}-{chunk.end_pos}")
        print(f"  텍스트: {chunk.text[:50]}...")

        if chunk.metadata and chunk.metadata.get('is_transition_point'):
            print(f"  🔄 전환점! 중요도: {chunk.metadata.get('transition_significance')}")
            print(f"  다음 감정: {chunk.metadata.get('next_emotion')}")

        print()

    # 통계 출력
    stats = get_emotion_statistics(chunks)
    print("\n청킹 통계:")
    print(f"  총 청크 수: {stats['total_chunks']}")
    print(f"  평균 길이: {stats['avg_chunk_length']:.1f}자")
    print(f"  감정 분포: {stats['emotion_distribution']}")

    return chunks


def example_vector_store():
    """벡터 스토어 예제"""
    print("\n" + "=" * 60)
    print("예제 2: 벡터 스토어에 저장 및 검색")
    print("=" * 60)

    # 샘플 텍스트
    sample_text = """
    AI 기술의 발전은 놀라울 따름이다. 매일 새로운 혁신이 일어난다.
    특히 자연어 처리 분야의 성장은 경이롭다.

    하지만 AI 윤리 문제는 여전히 우려스럽다.
    개인정보 보호와 편향성 문제가 심각하다.
    이러한 문제들을 해결하지 않으면 큰 위험이 될 수 있다.

    그럼에도 불구하고 AI의 긍정적 가능성은 무한하다.
    의료, 교육, 환경 문제 해결에 큰 도움이 될 것이다.
    우리는 희망을 가지고 앞으로 나아가야 한다.
    """

    # 1. 청킹
    print("\n1단계: 텍스트 청킹...")
    chunks = split_text_by_emotions(sample_text, max_chunk_size=300)

    # 2. 벡터 스토어 초기화
    print("\n2단계: 벡터 스토어 초기화...")
    vector_store = EmotionAwareVectorStore(
        collection_name="example_collection",
        persist_directory="./example_chroma_db"
    )

    # 3. 청크 저장
    print("\n3단계: 청크를 벡터 스토어에 저장...")
    vector_store.add_chunks(chunks, document_id="sample_doc")

    # 4. 검색 테스트
    print("\n4단계: 검색 테스트...")
    queries = [
        "AI의 긍정적인 측면",
        "우려되는 문제점",
        "미래에 대한 희망"
    ]

    for query in queries:
        print(f"\n쿼리: '{query}'")
        results = vector_store.search(query, k=2)

        for i, result in enumerate(results, 1):
            print(f"  결과 {i}:")
            print(f"    텍스트: {result['document'][:60]}...")
            print(f"    감정: {result['metadata'].get('emotion', 'N/A')}")
            print(f"    거리: {result['distance']:.4f}")

    # 통계
    stats = vector_store.get_stats()
    print(f"\n벡터 스토어 통계: {stats}")

    return vector_store


def example_advanced_retrieval():
    """고급 검색 예제"""
    print("\n" + "=" * 60)
    print("예제 3: 고급 검색 전략")
    print("=" * 60)

    # 긴 샘플 텍스트
    sample_text = """
    새로운 프로젝트가 시작되었다. 팀원들은 모두 열정적이었다.
    우리는 혁신적인 제품을 만들 것이라고 확신했다.

    개발 초기에는 모든 것이 순조로웠다. 프로토타입은 완벽했다.
    투자자들의 반응도 좋았다. 미래가 밝아 보였다.

    그러나 3개월 후 심각한 기술적 문제가 발생했다.
    핵심 기능이 작동하지 않았다. 팀의 사기가 급격히 떨어졌다.
    모두가 불안해했다. 프로젝트가 실패할 것 같았다.

    하지만 우리는 포기하지 않았다. 밤낮으로 문제를 분석했다.
    마침내 해결책을 찾아냈다. 새로운 접근 방식이 효과가 있었다.

    6개월 후 제품을 성공적으로 출시했다. 사용자 반응이 폭발적이었다.
    우리의 노력이 결실을 맺었다. 이보다 더 보람찬 순간은 없었다.
    """

    # 청킹 및 벡터 스토어 설정
    chunks = split_text_by_emotions(sample_text, max_chunk_size=200)

    vector_store = EmotionAwareVectorStore(
        collection_name="advanced_example",
        persist_directory="./example_chroma_db"
    )
    vector_store.add_chunks(chunks, document_id="project_story")

    # 리트리버 초기화
    retriever = EmotionAwareRetriever(vector_store)

    # 다양한 검색 전략 테스트
    query = "프로젝트의 위기 상황"

    print(f"\n쿼리: '{query}'\n")

    # 전략 1: 기본 검색
    print("전략 1: 기본 검색")
    basic_results = retriever.retrieve(query, k=2, strategy="basic")
    for i, r in enumerate(basic_results, 1):
        print(f"  {i}. {r['document'][:50]}... (거리: {r['distance']:.4f})")

    # 전략 2: 감정 부스트 검색
    print("\n전략 2: 감정 부스트 검색")
    boosted_results = retriever.retrieve(query, k=2, strategy="emotion_boosted")
    for i, r in enumerate(boosted_results, 1):
        sig = r['metadata'].get('transition_significance', 0)
        print(f"  {i}. {r['document'][:50]}... (중요도: {sig})")

    # 전략 3: 문맥 포함 검색
    print("\n전략 3: 문맥 포함 검색")
    contextual_results = retriever.retrieve(query, k=1, strategy="contextual", context_window=1)
    if contextual_results:
        print(f"  문맥 포함 텍스트:\n  {contextual_results[0].get('context', '')[:100]}...")

    # 전략 4: 하이브리드 검색
    print("\n전략 4: 하이브리드 검색")
    hybrid_results = retriever.retrieve(query, k=2, strategy="hybrid")
    for i, r in enumerate(hybrid_results, 1):
        print(f"  {i}. {r['document'][:50]}... (하이브리드 점수: {r.get('hybrid_score', 0):.4f})")

    # 감정 아크 추출
    print("\n감정 흐름 분석:")
    emotional_arc = retriever.get_emotional_arc("project_story")
    for chunk_info in emotional_arc[:5]:  # 처음 5개만
        print(f"  청크 {chunk_info['chunk_id']}: {chunk_info['emotion']}")

    # 시각화
    print("\n" + visualize_emotional_arc(chunks))

    return retriever


def example_with_real_file():
    """실제 파일로 작업하는 예제"""
    print("\n" + "=" * 60)
    print("예제 4: 실제 파일 처리")
    print("=" * 60)

    # 파일 경로 (존재하지 않으면 스킵)
    file_path = "./sample_text.txt"

    if not Path(file_path).exists():
        print(f"\n⚠️ 파일이 없습니다: {file_path}")
        print("샘플 파일을 생성합니다...")

        # 샘플 파일 생성
        sample_content = """
        여행의 시작은 설렘으로 가득했다.
        새로운 곳을 탐험한다는 생각만으로도 가슴이 뛰었다.

        하지만 첫날부터 문제가 생겼다.
        짐을 잃어버렸고, 숙소를 찾을 수 없었다.

        다행히 친절한 현지인의 도움을 받았다.
        그날 밤, 인간의 선의에 대해 다시 생각하게 되었다.
        """

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)

    # 파일 로드
    text = load_text_from_file(file_path)
    print(f"\n파일 로드 완료: {len(text)}자")

    # 청킹
    chunks = split_text_by_emotions(text, max_chunk_size=500)

    # JSON으로 저장
    output_path = "./chunks_output.json"
    save_chunks_to_json(chunks, output_path)

    print(f"\n청크 저장 완료: {output_path}")
    print(f"총 {len(chunks)}개 청크 생성")

    # 벡터 스토어에 추가
    vector_store = EmotionAwareVectorStore(
        collection_name="file_example",
        persist_directory="./example_chroma_db"
    )
    vector_store.add_chunks(chunks, document_id="travel_story")

    # 검색 테스트
    query = "여행 중 어려움"
    results = vector_store.search(query, k=2)

    print(f"\n검색 결과 ('{query}'):")
    for i, result in enumerate(results, 1):
        print(f"\n결과 {i}:")
        print(f"  {result['document']}")
        print(f"  감정: {result['metadata'].get('emotion')}")


def main():
    """모든 예제 실행"""
    print("\n" + "=" * 60)
    print("감정 기반 RAG 시스템 예제")
    print("=" * 60)

    try:
        # 예제 1: 기본 청킹
        example_basic_chunking()

        # 예제 2: 벡터 스토어
        example_vector_store()

        # 예제 3: 고급 검색
        example_advanced_retrieval()

        # 예제 4: 파일 처리
        example_with_real_file()

        print("\n" + "=" * 60)
        print("모든 예제 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
