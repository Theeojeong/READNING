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
from services.langgraph_workflow import music_workflow
from utils.file_utils import secure_filename
from utils.logger import log
from config import GEN_DURATION, OUTPUT_DIR


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
    abs_bookdir = os.path.join(OUTPUT_DIR, book_dir)
    
    if not os.path.exists(abs_bookdir):
        os.makedirs(abs_bookdir)
    
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
    
    # 페이지별 청크 매핑 생성 (한 페이지당 4개 청크 고정)
    page_chunk_mapping = {}
    CHUNKS_PER_PAGE = 4  # 한 페이지당 청크 수 고정
    
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
        "processing_method": "async_emotion_detection_parallel",
        "performance_optimizations": {
            "max_concurrent_emotion_analysis": 8,
            "max_concurrent_music_generation": 4,
            "emotion_analysis_timeout": 45.0
        }
    }



@router.post("/music-langgraph")
async def generate_music_with_langgraph(
    file: UploadFile = File(), 
    user_name: str = Form(), 
    book_title: str = Form()
):
    """
    🚀 LangGraph 기반 음악 생성 워크플로우:
    1. 텍스트 분리 → 2. 감정 분석 → 3. 청크 생성 → 4. 음악 생성 → 5. DB 저장
    모든 단계가 그래프로 관리되어 시각화 및 디버깅이 용이함
    """
    
    book_title = secure_filename(book_title)
    book_id = f"{user_name}_{book_title}"
    
    # 디렉토리 설정
    book_dir = f"{user_name}/{book_title}"
    abs_bookdir = os.path.join(OUTPUT_DIR, book_dir)
    
    if not os.path.exists(abs_bookdir):
        os.makedirs(abs_bookdir)
    
    # 텍스트 읽기
    text = file.file.read().decode("utf-8")
    text_length = len(text)
    log(f"📄 LangGraph: 텍스트 길이 {text_length:,}자")
    
    # LangGraph 워크플로우 실행
    result = await music_workflow.run_workflow(
        text=text,
        user_name=user_name,
        book_title=book_title,
        book_id=book_id,
        book_dir=book_dir
    )
    
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
