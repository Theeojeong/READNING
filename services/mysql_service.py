"""
MySQL 데이터베이스 서비스
청크 텍스트와 음악 메타데이터를 저장/조회합니다.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# MySQL 연결 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://readning_user:readning_pass@localhost:3307/readning"
)

print(f"[MySQL] 연결 URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")

try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # 개발 시 True로 변경하면 SQL 쿼리 출력
        pool_pre_ping=True,  # 연결 끊김 자동 복구
        pool_recycle=3600,  # 1시간마다 연결 재생성
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    print("[MySQL] ✅ 데이터베이스 연결 성공")
except Exception as e:
    print(f"[MySQL] ❌ 연결 실패: {e}")
    raise


class MySQLService:
    """MySQL 데이터베이스 작업을 처리하는 서비스 클래스"""

    @staticmethod
    def save_chapter_chunks(
        book_id: str,
        page: int,
        chunks: List[Dict[str, Any]],
        total_duration: int,
        book_title: str = "",
    ) -> int:
        """
        챕터와 청크 데이터 저장
        
        Args:
            book_id: 책 ID (예: "user123_book_title")
            page: 페이지 번호
            chunks: 청크 데이터 리스트
            total_duration: 전체 음악 길이 (초)
            book_title: 책 제목 (선택)
        
        Returns:
            chapter_id: 생성된 챕터 ID
        """
        session = SessionLocal()
        try:
            # 0) 책 데이터 먼저 생성 (없으면 생성)
            user_id = book_id.split('_')[0] if '_' in book_id else "unknown"
            session.execute(
                text("""
                    INSERT INTO books (id, user_id, title)
                    VALUES (:book_id, :user_id, :title)
                    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "book_id": book_id,
                    "user_id": user_id,
                    "title": book_title or book_id
                }
            )
            session.commit()

            # 1) 챕터 저장 (이미 있으면 업데이트)
            session.execute(
                text("""
                    INSERT INTO chapters (book_id, page, total_duration)
                    VALUES (:book_id, :page, :duration)
                    ON DUPLICATE KEY UPDATE 
                        total_duration = :duration,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {"book_id": book_id, "page": page, "duration": total_duration}
            )
            session.commit()

            # 챕터 ID 가져오기
            chapter = session.execute(
                text("SELECT id FROM chapters WHERE book_id = :book_id AND page = :page"),
                {"book_id": book_id, "page": page}
            ).fetchone()

            if not chapter:
                raise Exception(f"챕터 생성 실패: {book_id}, page {page}")

            chapter_id = chapter[0]
            print(f"[MySQL] 📖 챕터 저장 완료: chapter_id={chapter_id}, book={book_id}, page={page}")

            # 2) 기존 청크 삭제 (재생성 방지)
            session.execute(
                text("DELETE FROM chunks WHERE chapter_id = :chapter_id"),
                {"chapter_id": chapter_id}
            )

            # 3) 새 청크 저장
            for chunk in chunks:
                session.execute(
                    text("""
                        INSERT INTO chunks 
                        (chapter_id, chunk_index, text_content, text_preview, 
                         emotion, audio_url, audio_duration)
                        VALUES (:chapter_id, :idx, :text, :preview, 
                                :emotion, :audio_url, :duration)
                    """),
                    {
                        "chapter_id": chapter_id,
                        "idx": chunk["index"],
                        "text": chunk["fullText"],
                        "preview": chunk["text"][:500] if len(chunk["text"]) > 500 else chunk["text"],
                        "emotion": chunk["emotion"],
                        "audio_url": chunk["audioUrl"],
                        "duration": chunk.get("duration", 30.0)
                    }
                )

            session.commit()
            print(f"[MySQL] 🎵 청크 {len(chunks)}개 저장 완료")

            return chapter_id

        except Exception as e:
            session.rollback()
            print(f"[MySQL] ❌ 저장 실패: {e}")
            raise e
        finally:
            session.close()

    @staticmethod
    def get_chapter_chunks(book_id: str, page: int) -> Optional[Dict[str, Any]]:
        """
        챕터의 청크 데이터 조회
        
        Args:
            book_id: 책 ID
            page: 페이지 번호
        
        Returns:
            챕터 데이터 (청크 리스트 포함) 또는 None
        """
        session = SessionLocal()
        try:
            # 챕터 조회
            chapter = session.execute(
                text("""
                    SELECT id, total_duration, created_at
                    FROM chapters 
                    WHERE book_id = :book_id AND page = :page
                """),
                {"book_id": book_id, "page": page}
            ).fetchone()

            if not chapter:
                print(f"[MySQL] ⚠️ 챕터 없음: {book_id}, page {page}")
                return None

            chapter_id, total_duration, created_at = chapter

            # 청크 조회 (순서대로)
            chunks = session.execute(
                text("""
                    SELECT chunk_index, text_content, text_preview, 
                           emotion, audio_url, audio_duration
                    FROM chunks
                    WHERE chapter_id = :chapter_id
                    ORDER BY chunk_index ASC
                """),
                {"chapter_id": chapter_id}
            ).fetchall()

            print(f"[MySQL] ✅ 조회 성공: {book_id}, page {page}, 청크 {len(chunks)}개")

            return {
                "page": page,
                "bookId": book_id,
                "totalDuration": total_duration,
                "createdAt": created_at.isoformat() if created_at else None,
                "chunks": [
                    {
                        "index": row[0],
                        "fullText": row[1],
                        "text": row[2],
                        "emotion": row[3],
                        "audioUrl": row[4],
                        "duration": row[5]
                    }
                    for row in chunks
                ]
            }

        except Exception as e:
            print(f"[MySQL] ❌ 조회 실패: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_all_chapters(book_id: str) -> List[Dict[str, Any]]:
        """책의 모든 챕터 목록 조회"""
        session = SessionLocal()
        try:
            chapters = session.execute(
                text("""
                    SELECT page, total_duration, 
                           (SELECT COUNT(*) FROM chunks WHERE chapter_id = chapters.id) as chunk_count,
                           created_at
                    FROM chapters
                    WHERE book_id = :book_id
                    ORDER BY page ASC
                """),
                {"book_id": book_id}
            ).fetchall()

            return [
                {
                    "page": row[0],
                    "totalDuration": row[1],
                    "chunkCount": row[2],
                    "createdAt": row[3].isoformat() if row[3] else None
                }
                for row in chapters
            ]

        finally:
            session.close()

    @staticmethod
    def health_check() -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            session = SessionLocal()
            session.execute(text("SELECT 1"))
            session.close()
            return True
        except Exception as e:
            print(f"[MySQL] 헬스체크 실패: {e}")
            return False


# 싱글톤 인스턴스
mysql_service = MySQLService()


# 모듈 로드 시 연결 테스트
if __name__ == "__main__":
    print("=== MySQL 서비스 테스트 ===")
    if mysql_service.health_check():
        print("✅ 데이터베이스 연결 정상")
    else:
        print("❌ 데이터베이스 연결 실패")

