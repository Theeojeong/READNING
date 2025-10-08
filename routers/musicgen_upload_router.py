import json
import os
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from fastapi.responses import FileResponse

from services.ebooks2text import split_txt_into_pages, convert_and_split
from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
)
from utils.file_utils import (
    save_text_to_file,
    ensure_dir,
    secure_filename,
)
from config import (
    OUTPUT_DIR,
    FINAL_MIX_NAME,
    GEN_DURATION,
    TOTAL_DURATION,
)
from typing import List
from pathlib import Path

router = APIRouter(prefix="/generate", tags=["UploadWorkflow"])


@router.get("/health")
async def health_check():
    """
    시스템 헬스체크
    - MySQL 연결 상태
    - 디스크 공간
    - MusicGen 모델 로드 여부
    """
    import shutil
    from services.mysql_service import mysql_service
    from services.model_manager import musicgen_manager
    
    health_status = {
        "status": "healthy",
        "timestamp": str(__import__('datetime').datetime.now()),
        "checks": {}
    }
    
    # 1) MySQL 연결 체크
    try:
        mysql_healthy = mysql_service.health_check()
        health_status["checks"]["mysql"] = {
            "status": "ok" if mysql_healthy else "error",
            "message": "MySQL 연결 정상" if mysql_healthy else "MySQL 연결 실패"
        }
    except Exception as e:
        health_status["checks"]["mysql"] = {
            "status": "error",
            "message": f"MySQL 체크 실패: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # 2) 디스크 공간 체크
    try:
        disk_usage = shutil.disk_usage(OUTPUT_DIR)
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        health_status["checks"]["disk"] = {
            "status": "ok" if free_gb > 1 else "warning",
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "usage_percent": round(usage_percent, 2),
            "message": f"여유 공간 {round(free_gb, 2)}GB"
        }
        
        if free_gb < 1:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "error",
            "message": f"디스크 체크 실패: {str(e)}"
        }
    
    # 3) MusicGen 모델 체크
    try:
        model_loaded = musicgen_manager.model is not None
        health_status["checks"]["musicgen"] = {
            "status": "ok" if model_loaded else "not_loaded",
            "message": "MusicGen 모델 로드됨" if model_loaded else "모델 미로드 (첫 요청 시 로드됨)"
        }
    except Exception as e:
        health_status["checks"]["musicgen"] = {
            "status": "error",
            "message": f"모델 체크 실패: {str(e)}"
        }
    
    # 4) 출력 디렉토리 체크
    try:
        output_exists = os.path.exists(OUTPUT_DIR)
        health_status["checks"]["output_dir"] = {
            "status": "ok" if output_exists else "error",
            "path": OUTPUT_DIR,
            "message": "출력 디렉토리 정상" if output_exists else "출력 디렉토리 없음"
        }
        
        if not output_exists:
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["output_dir"] = {
            "status": "error",
            "message": f"디렉토리 체크 실패: {str(e)}"
        }
    
    # 전체 상태 코드 결정
    if health_status["status"] == "unhealthy":
        raise HTTPException(503, detail=health_status)
    
    return health_status


@router.post("/music-v3-long")
async def generate_music_long(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    book_title: str = Form(...),
    page: int = Form(..., ge=0),
    target_len: int = Form(240),
):
    """
    텍스트를 감정 기반으로 청크 분할하고, 각 청크별로 음악을 생성합니다.
    병합하지 않고 개별 청크 파일로 저장하여 동적 리더에서 사용합니다.
    """
    safe_title = secure_filename(book_title)

    # 이미 생성된 데이터가 MySQL에 있는지 확인
    from services.mysql_service import mysql_service
    book_id = f"{user_id}_{safe_title}"
    existing_data = mysql_service.get_chapter_chunks(book_id, page)
    
    if existing_data and len(existing_data.get('chunks', [])) > 0:
        print(f"[music-v3-long] ⚡ 캐시된 데이터 사용: {book_id}, page {page}")
        return {
            "message": f"{safe_title} p{page} 이미 생성됨 (캐시 사용)",
            "page": page,
            "chunks": len(existing_data['chunks']),
            "book_id": book_id,
            "cached": True
        }

    # 0) 디렉토리 설정 ------------------------------------------------
    book_dir = f"{user_id}/{safe_title}"
    abs_bookdir = os.path.join(OUTPUT_DIR, book_dir)
    ensure_dir(abs_bookdir)

    # 1) 텍스트 읽기 --------------------------------------------------
    text = file.file.read().decode("utf-8")
    
    # 4) 청크 분할 ----------------------------------------------------
    try:
        chunks = chunk_text_by_emotion.chunk_text_by_emotion(text)
    except Exception as e:
        print("[music-v3-long] chunking error:", e)
        raise HTTPException(500, "텍스트 청크 분할 중 오류가 발생했습니다")

    # 5) MusicGen ----------------------------------------------------
    try:
        global_prompt = prompt_service.generate_global(text)
        rp = []
        for chunk in chunks:
            ctxt = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            regional = prompt_service.generate_regional(ctxt)
            rp.append(
                prompt_service.compose_musicgen_prompt(global_prompt, f"{regional}")
            )
        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=rp,
            book_id_dir=book_dir,
        )
    except Exception as e:
        print("[music-v3-long] musicgen error:", e)
        raise HTTPException(500, "음악 생성 중 오류가 발생했습니다")

    # 6) MySQL에 메타데이터 저장 --------------------------------------
    try:
        # 청크 메타데이터 준비
        chunk_metadata = []
        for idx, chunk in enumerate(chunks):
            chunk_text = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            chunk_context = chunk[1] if isinstance(chunk, (list, tuple)) and len(chunk) > 1 else {}
            
            chunk_metadata.append({
                "index": idx + 1,
                "text": chunk_text[:500],  # 프리뷰용
                "fullText": chunk_text,
                "emotion": chunk_context.get("emotions", "unknown"),
                "audioUrl": f"/{OUTPUT_DIR}/{book_dir}/chunk_{idx+1}.wav",
                "duration": GEN_DURATION / 1000.0
            })
        
        # MySQL에 저장
        mysql_service.save_chapter_chunks(
            book_id=f"{user_id}_{safe_title}",
            page=page,
            chunks=chunk_metadata,
            total_duration=target_len,
            book_title=book_title
        )
        print(f"[music-v3-long] ✅ MySQL 저장 완료: {len(chunk_metadata)} 청크")
    except Exception as e:
        print(f"[music-v3-long] ⚠️ MySQL 저장 실패 (계속 진행): {e}")

    # 7) 응답 --------------------------------------------------------
    return {
        "message": f"{safe_title} p{page} 음원 생성 완료",
        "page": page,
        "chunks": len(chunks),
        "book_id": f"{user_id}_{safe_title}",
        "audio_files": [f"/{OUTPUT_DIR}/{book_dir}/chunk_{i+1}.wav" for i in range(len(chunks))]
    }
