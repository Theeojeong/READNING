import os
from typing import List, Dict, Any
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from services.model_manager import musicgen_manager
from services.mysql_service import mysql_service
from services import prompt_service
from services.async_emotion_analysis import process_book_with_async_emotion_detection
from services.async_music_generation import process_all_chunks_async
from services.workflow_refactored import music_workflow_refactored
from utils.file_utils import secure_filename
from utils.logger import log
from config import GEN_DURATION, OUTPUT_DIR, CHUNKS_PER_PAGE
import json
from services.text_processing_service import text_processing_service


router = APIRouter(prefix="/generate")


@router.post("/music")
async def generate_music_optimized(
    file: UploadFile = File(),
    user_name: str = Form(),
    book_title: str = Form()
):

    book_title = secure_filename(book_title)
    book_id = f"{user_name}_{book_title}"

    # 디렉토리 설정
    book_dir = f"{user_name}/{book_title}"
    abs_book_dir = os.path.join(OUTPUT_DIR, book_dir)
    if not os.path.exists(abs_book_dir):
        os.makedirs(abs_book_dir)

    # 텍스트 읽기
    text = file.file.read().decode("utf-8")
    text_length = len(text)
    print(f"📄 텍스트 길이: {text_length:,}자")

    # 글로벌 프롬프트 생성 (전체 텍스트 기반)
    global_prompt = prompt_service.generate_global(text)

    # 비동기 감정 분석 워크플로우 실행
    log("🎭 비동기 감정 분석 워크플로우 시작")
    all_chunks = await process_book_with_async_emotion_detection(text)

    total_chunks = len(all_chunks)
    log(f"🎭 비동기 감정 분석 완료: 총 {total_chunks}개 청크 생성")

    # 페이지별 청크 매핑 생성 (한 페이지당 고정 청크 수)
    page_chunk_mapping = {}

    for i, chunk in enumerate[Dict[str, Any]](all_chunks):
        page_num = (i // CHUNKS_PER_PAGE) + 1
        if page_num not in page_chunk_mapping:
            page_chunk_mapping[page_num] = {
                "start_index": i + 1,
                "end_index": i + 1,
                "chunk_count": 0
            }
        page_chunk_mapping[page_num]["end_index"] = i + 1
        page_chunk_mapping[page_num]["chunk_count"] += 1
        chunk["page"] = page_num

    log(f"📄 페이지 구성: 총 {len(page_chunk_mapping)}페이지, 페이지당 {CHUNKS_PER_PAGE}개 청크")

    # 모든 청크를 비동기 병렬 처리
    print(f"🎵 {total_chunks}개 청크 음악 생성 시작...")
    chunk_metadata = await process_all_chunks_async(all_chunks, book_dir, global_prompt)

    # 페이지별로 청크 그룹화 및 저장
    page_results = []

    for page_num, mapping in page_chunk_mapping.items():
        start_idx = mapping["start_index"] - 1  # 0-based index
        end_idx = mapping["end_index"]

        # 해당 페이지의 청크들만 추출
        page_chunks = chunk_metadata[start_idx:end_idx]

        if not page_chunks:
            page_results.append({
                "page": page_num,
                "chunks": 0,
                "duration": 0,
                "error": "청크 생성 실패"
            })
            continue

        # 페이지별 음악 길이 계산
        page_duration = len(page_chunks) * GEN_DURATION

        # MySQL에 저장
        try:
            mysql_service.save_chapter_chunks(
                book_id=book_id,
                page=page_num,
                chunks=page_chunks,
                total_duration=page_duration,
                book_title=book_title,
            )

            page_results.append({
                "page": page_num,
                "chunks": len(page_chunks),
                "duration": page_duration,
                "cached": False
            })

            print(f"✅ 페이지 {page_num} 저장 완료: {len(page_chunks)}개 청크, {page_duration}초")

        except Exception as e:
            print(f"❌ 페이지 {page_num} 저장 실패: {e}")
            page_results.append({
                "page": page_num,
                "error": str(e),
                "cached": False
            })

    # 응답
    total_duration = sum(page.get("duration", 0) for page in page_results)
    successful_pages = len([p for p in page_results if "error" not in p])

    return {
        "message": f"{book_title} 음악 생성 완료",
        "book_id": book_id,
        "text_length": text_length,
        "total_pages": len(page_chunk_mapping),
        "total_chunks": total_chunks,
        "total_duration": total_duration,
        "successful_pages": successful_pages,
        "pages": page_results,
    }



@router.post("/music-v3")
async def generate_music_v3(
    file: UploadFile = File(...),
    book_id: str = Form(...),
    user_name: str = Form(default="guest"),
    book_title: str = Form(default="untitled")
):
    """
    Music Generation V3
    - Supports PDF, EPUB, TXT
    """

    # If book_title is default but file has name, use filename
    if book_title == "untitled" and file.filename:
        book_title = os.path.splitext(file.filename)[0]
    
    book_title = secure_filename(book_title)
    # Use the provided book_id or construct one if needed. 
    # For consistency with file storage, we use user_name and book_title for directory.
    # But we pass the provided book_id to MySQL if that's what frontend expects.
    
    # Directory setup
    book_dir = f"{user_name}/{book_title}"
    abs_book_dir = os.path.join(OUTPUT_DIR, book_dir)
    if not os.path.exists(abs_book_dir):
        os.makedirs(abs_book_dir)

    # Text Extraction
    try:
        text = await text_processing_service.extract_text(file)
    except Exception as e:
        raise HTTPException(400, f"Text extraction failed: {str(e)}")

    text_length = len(text)
    print(f"📄 Text Length: {text_length:,} chars")

    if text_length < 50:
        raise HTTPException(400, "Text is too short to generate music.")

    # Global Prompt (No Preferences)
    global_prompt = prompt_service.generate_global(text)

    # Async Emotion Analysis
    log("🎭 Starting Async Emotion Analysis Workflow")
    all_chunks = await process_book_with_async_emotion_detection(text)
    total_chunks = len(all_chunks)
    log(f"🎭 Emotion Analysis Complete: {total_chunks} chunks")

    # Page Mapping
    page_chunk_mapping = {}
    for i, chunk in enumerate(all_chunks):
        page_num = (i // CHUNKS_PER_PAGE) + 1
        if page_num not in page_chunk_mapping:
            page_chunk_mapping[page_num] = {
                "start_index": i + 1,
                "end_index": i + 1,
                "chunk_count": 0
            }
        page_chunk_mapping[page_num]["end_index"] = i + 1
        page_chunk_mapping[page_num]["chunk_count"] += 1
        chunk["page"] = page_num

    log(f"📄 Page Config: {len(page_chunk_mapping)} pages, {CHUNKS_PER_PAGE} chunks/page")

    # Async Music Generation
    print(f"🎵 Generating music for {total_chunks} chunks...")
    chunk_metadata = await process_all_chunks_async(all_chunks, book_dir, global_prompt)

    # Save Results
    page_results = []

    for page_num, mapping in page_chunk_mapping.items():
        start_idx = mapping["start_index"] - 1
        end_idx = mapping["end_index"]
        page_chunks = chunk_metadata[start_idx:end_idx]

        if not page_chunks:
            page_results.append({
                "page": page_num,
                "chunks": 0,
                "duration": 0,
                "error": "Chunk generation failed"
            })
            continue

        page_duration = len(page_chunks) * GEN_DURATION

        try:
            mysql_service.save_chapter_chunks(
                book_id=book_id, # Use the ID from frontend
                page=page_num,
                chunks=page_chunks,
                total_duration=page_duration,
                book_title=book_title,
            )

            page_results.append({
                "page": page_num,
                "chunks": len(page_chunks),
                "duration": page_duration,
                "cached": False
            })
            print(f"✅ Page {page_num} saved: {len(page_chunks)} chunks")

        except Exception as e:
            print(f"❌ Page {page_num} save failed: {e}")
            page_results.append({
                "page": page_num,
                "error": str(e),
                "cached": False
            })

    total_duration = sum(page.get("duration", 0) for page in page_results)
    successful_pages = len([p for p in page_results if "error" not in p])

    return {
        "message": f"{book_title} Music Generation Complete",
        "book_id": book_id,
        "text_length": text_length,
        "total_pages": len(page_chunk_mapping),
        "total_chunks": total_chunks,
        "total_duration": total_duration,
        "successful_pages": successful_pages,
        "chapters": page_results, # Frontend expects "chapters"
    }

@router.post("/music-langgraph")
async def generate_music_with_langgraph(
    file: UploadFile = File(),
    user_name: str = Form(),
    book_title: str = Form()
):
    """
    🚀 Refactored LangGraph-based music generation workflow.

    This endpoint uses Clean Architecture principles for:
    - Single Responsibility: Each component has ONE clear purpose
    - Dependency Injection: Services are testable and swappable
    - Type Safety: Strong typing throughout the pipeline
    - Error Handling: Functional error handling with Result types
    - Observability: Detailed performance metrics and logging

    Improvements over legacy /music endpoint:
    1. Emotion-based chunking - Splits at emotional transitions
    2. Significance filtering - Only processes important changes
    3. Automatic position calculation - No manual position tracking
    4. Batch processing - Concurrent emotion analysis
    5. Comprehensive metrics - Per-step timing and statistics

    Args:
        file: Text file to process (.txt format)
        user_name: User identifier for directory organization
        book_title: Title of the book/text

    Returns:
        WorkflowResult with:
        - Generated music files and metadata
        - Page-by-page breakdown
        - Performance metrics
        - Error details (if any)

    Raises:
        HTTPException: On validation or processing failures
    """
    # Input validation
    book_title = secure_filename(book_title)
    book_id = f"{user_name}_{book_title}"

    # Setup output directory
    book_dir = f"{user_name}/{book_title}"
    abs_book_dir = os.path.join(OUTPUT_DIR, book_dir)
    if not os.path.exists(abs_book_dir):
        os.makedirs(abs_book_dir)

    # Read and validate text
    text = file.file.read().decode("utf-8")
    text_length = len(text)

    if text_length < 100:
        raise HTTPException(
            status_code=400,
            detail="Text too short. Minimum 100 characters required."
        )

    log(f"📄 Processing: {book_title} ({text_length:,} chars)")

    # Execute refactored workflow
    result = await music_workflow_refactored.run_workflow(
        text=text,
        user_name=user_name,
        book_title=book_title,
        book_id=book_id,
        book_dir=book_dir
    )

    # Check for errors
    if result.get("errors"):
        log(f"⚠️ Workflow completed with errors: {result['errors']}")

    # Return comprehensive result
    return result



@router.get("/health")
async def health_check():

    health_status = {
        "status": "healthy",
        "timestamp": str(__import__("datetime").datetime.now()),
        "checks": {},
    }

    # MySQL 연결 체크
    try:
        mysql_healthy = mysql_service.health_check()
        health_status["checks"]["mysql"] = {
            "status": "ok" if mysql_healthy else "error",
            "message": "MySQL 연결 정상" if mysql_healthy else "MySQL 연결 실패",
        }
    except Exception as e:
        health_status["checks"]["mysql"] = {
            "status": "error",
            "message": f"MySQL 체크 실패: {str(e)}",
        }
        health_status["status"] = "unhealthy"

    # MusicGen 모델 체크
    try:
        model_loaded = musicgen_manager.model is not None
        health_status["checks"]["musicgen"] = {
            "status": "ok" if model_loaded else "not_loaded",
            "message": (
                "MusicGen 모델 로드됨"
                if model_loaded
                else "모델 미로드 (첫 요청 시 로드됨)"
            ),
        }
    except Exception as e:
        health_status["checks"]["musicgen"] = {
            "status": "error",
            "message": f"모델 체크 실패: {str(e)}",
        }

    # 4) 출력 디렉토리 체크
    try:
        output_exists = os.path.exists(OUTPUT_DIR)
        health_status["checks"]["output_dir"] = {
            "status": "ok" if output_exists else "error",
            "path": OUTPUT_DIR,
            "message": "출력 디렉토리 정상" if output_exists else "출력 디렉토리 없음",
        }

        if not output_exists:
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["output_dir"] = {
            "status": "error",
            "message": f"디렉토리 체크 실패: {str(e)}",
        }

    # 전체 상태 코드 결정
    if health_status["status"] == "unhealthy":
        raise HTTPException(503, detail=health_status)

    return health_status


@router.post("/music-by-chapter")
async def get_music_by_chapter(
    book_id: str = Form(...),
    chapter_index: str = Form(...),
    chapter_title: str = Form(default=""),
    text: str = Form(default="")
):
    """
    챕터별 음악 데이터 조회 (EpubViewer용)
    이미 생성된 데이터를 MySQL에서 조회하여 반환합니다.
    """
    try:
        # EpubViewer는 0-based index를 사용하지만, DB는 1-based page를 사용
        page = int(chapter_index) + 1
        
        log(f"🎵 챕터 음악 조회 요청: book_id={book_id}, page={page}")
        
        result = mysql_service.get_chapter_chunks(book_id, page)
        
        if result:
            return result
        else:
            # 데이터가 없으면 빈 리스트 반환 (또는 여기서 실시간 생성 로직 추가 가능)
            log(f"⚠️ 챕터 데이터 없음: {book_id}, page {page}")
            return {"chunks": []}
            
    except Exception as e:
        log(f"❌ 챕터 조회 실패: {e}")
        raise HTTPException(500, str(e))
