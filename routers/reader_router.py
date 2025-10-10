"""
Reader API 라우터
프론트엔드에서 청크+음악 데이터를 조회하는 API
"""

from fastapi import APIRouter, HTTPException
from services.mysql_service import mysql_service
from typing import Dict, Any

router = APIRouter(prefix="/api/reader", tags=["Reader"])


@router.get("/health")
async def health_check():
    """데이터베이스 연결 상태 확인"""
    if mysql_service.health_check():
        return {"status": "ok", "database": "connected"}
    else:
        raise HTTPException(503, "데이터베이스 연결 실패")


@router.get("/{user_id}")
async def get_user_books(user_id: str):
    """
    사용자가 업로드한 모든 책 목록 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        {
            "userId": "user123",
            "books": [
                {
                    "bookId": "user123_book1",
                    "title": "Book 1",
                    "author": "Author 1", 
                    "totalPages": 5,
                    "totalChunks": 15,
                    "totalDuration": 225.0,
                    "createdAt": "2024-01-01T10:00:00",
                    "updatedAt": "2024-01-01T10:00:00"
                },
                ...
            ]
        }
    """
    books = mysql_service.get_user_books(user_id)
    
    return {
        "userId": user_id,
        "totalBooks": len(books),
        "books": books
    }


@router.get("/{user_id}/{book_title}/{page}")
async def get_chapter_data(user_id: str, book_title: str, page: int):
    """
    특정 페이지의 청크+음악 데이터 조회
    
    Args:
        user_id: 사용자 ID
        book_title: 책 제목 (URL safe)
        page: 페이지 번호
    
    Returns:
        {
            "page": 1,
            "bookId": "user123_book_title",
            "totalDuration": 240,
            "chunks": [
                {
                    "index": 1,
                    "text": "...",
                    "fullText": "...",
                    "emotion": "peaceful",
                    "audioUrl": "/gen_musics/user123/book_title/chunk_1.wav",
                    "duration": 30.0
                },
                ...
            ]
        }
    """
    book_id = f"{user_id}_{book_title}"
    data = mysql_service.get_chapter_chunks(book_id, page)

    if not data:
        raise HTTPException(
            404,
            detail=f"페이지 데이터를 찾을 수 없습니다: {book_title} p{page}"
        )

    return data


@router.get("/{user_id}/{book_title}")
async def get_book_chapters(user_id: str, book_title: str):
    """
    책의 모든 챕터 목록 조회
    
    Returns:
        [
            {"page": 1, "totalDuration": 240, "chunkCount": 5},
            {"page": 2, "totalDuration": 180, "chunkCount": 3},
            ...
        ]
    """
    book_id = f"{user_id}_{book_title}"
    chapters = mysql_service.get_all_chapters(book_id)

    if not chapters:
        raise HTTPException(
            404,
            detail=f"책을 찾을 수 없습니다: {book_title}"
        )

    return {
        "bookId": book_id,
        "chapters": chapters
    }

