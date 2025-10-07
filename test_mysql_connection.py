"""MySQL 연결 테스트 스크립트"""

import os
os.environ["DATABASE_URL"] = "mysql+pymysql://readning_user:readning_pass@localhost:3307/readning"

from services.mysql_service import mysql_service

print("=" * 60)
print("🧪 MySQL 연결 테스트")
print("=" * 60)

# 1) 연결 테스트
print("\n[1] 헬스 체크...")
if mysql_service.health_check():
    print("✅ 데이터베이스 연결 성공!")
else:
    print("❌ 데이터베이스 연결 실패")
    exit(1)

# 2) 샘플 데이터 저장 테스트
print("\n[2] 샘플 데이터 저장...")
sample_chunks = [
    {
        "index": 1,
        "text": "새로운 하루가 시작됩니다...",
        "fullText": "새로운 하루가 시작됩니다. 창밖으로 부드러운 햇살이 들어오고, 새들의 지저귐이 들립니다.",
        "emotion": "peaceful",
        "audioUrl": "/gen_musics/test_user/test_book/chunk_1.wav",
        "duration": 30.0
    },
    {
        "index": 2,
        "text": "첫 발걸음을 내딛습니다...",
        "fullText": "첫 발걸음을 내딛습니다. 길은 때로는 평탄하고, 때로는 험난합니다.",
        "emotion": "adventurous",
        "audioUrl": "/gen_musics/test_user/test_book/chunk_2.wav",
        "duration": 30.0
    }
]

try:
    chapter_id = mysql_service.save_chapter_chunks(
        book_id="test_user_test_book",
        page=1,
        chunks=sample_chunks,
        total_duration=240,
        book_title="테스트 소설"
    )
    print(f"✅ 저장 성공! chapter_id={chapter_id}")
except Exception as e:
    print(f"❌ 저장 실패: {e}")
    exit(1)

# 3) 데이터 조회 테스트
print("\n[3] 데이터 조회...")
data = mysql_service.get_chapter_chunks("test_user_test_book", 1)
if data:
    print(f"✅ 조회 성공!")
    print(f"   페이지: {data['page']}")
    print(f"   총 시간: {data['totalDuration']}초")
    print(f"   청크 개수: {len(data['chunks'])}")
    for chunk in data['chunks']:
        print(f"     - Chunk {chunk['index']}: {chunk['emotion']} - {chunk['text'][:30]}...")
else:
    print("❌ 조회 실패")

print("\n" + "=" * 60)
print("🎉 모든 테스트 완료!")
print("=" * 60)

