import os
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from services.model_manager import musicgen_manager
from services.mysql_service import mysql_service
from services.ebooks2text import split_txt_into_pages
from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
)
from utils.file_utils import secure_filename
from config import GEN_DURATION

OUTPUT_DIR = "gen_musics"

router = APIRouter(prefix="/generate", tags=["UploadWorkflow"])

@router.post("/music")
async def generate_music_long(file: UploadFile = File(), user_name: str = Form(), book_title: str = Form()):

    book_title = secure_filename(book_title)
    book_id = f"{user_name}_{book_title}"

    # 디렉토리 설정
    book_dir = f"{user_name}/{book_title}"
    abs_bookdir = os.path.join(OUTPUT_DIR, book_dir)
    if not os.path.exists(abs_bookdir):
        os.makedirs(abs_bookdir)

    # 텍스트 읽기 및 자동 페이지 분할
    text = file.file.read().decode("utf-8")


    print(f"텍스트 길이: {len(text)}자")

    # 자동 페이지 분할
    pages = split_txt_into_pages(text)
    total_pages = len(pages)
    print(f"총 {total_pages} 페이지로 자동 분할")

    page_results = []

    # 각 페이지별 처리
    for page_num, page_text in enumerate(pages, 1):
        print(f"페이지 {page_num}/{total_pages} 처리 중...")

        # 이미 생성된 데이터 확인
        existing_data = mysql_service.get_chapter_chunks(book_id, page_num)

        if existing_data and len(existing_data.get("chunks", [])) > 0:
            print(f"페이지 {page_num} 캐시 사용")
            page_results.append(
                {
                    "page": page_num,
                    "chunks": len(existing_data["chunks"]),
                    "cached": True,
                }
            )
            continue

        try:
            # 2) 청크 분할
            chunks = chunk_text_by_emotion.chunk_text_by_emotion(page_text)
            print(f"✂️ 청크 {len(chunks)}개 생성")

            # 3) MusicGen 음악 생성
            global_prompt = prompt_service.generate_global(page_text)
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
                book_id_dir=f"{book_dir}/page{page_num}",
            )

            # 4) MySQL 메타데이터 저장
            chunk_metadata = []
            for idx, chunk in enumerate(chunks):
                chunk_text = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                chunk_context = (
                    chunk[1]
                    if isinstance(chunk, (list, tuple)) and len(chunk) > 1
                    else {}
                )

                chunk_metadata.append(
                    {
                        "index": idx + 1,
                        "text": chunk_text[:500],
                        "fullText": chunk_text,
                        "emotion": chunk_context.get("emotions", "unknown"),
                        "audioUrl": f"/{OUTPUT_DIR}/{book_dir}/page{page_num}/chunk_{idx+1}.wav",
                        "duration": GEN_DURATION,  # 초 단위 (15초)
                    }
                )

            # 실제 음악 총 길이 계산
            actual_duration = len(chunks) * GEN_DURATION

            mysql_service.save_chapter_chunks(
                book_id=book_id,
                page=page_num,
                chunks=chunk_metadata,
                total_duration=actual_duration,  # 실제 계산된 길이
                book_title=book_title,
            )

            page_results.append(
                {
                    "page": page_num,
                    "chunks": len(chunks),
                    "duration": actual_duration,  # 실제 음악 길이 (초)
                    "cached": False,
                }
            )

            print(f"✅ 페이지 {page_num} 완료")

        except Exception as e:
            print(f"❌ 페이지 {page_num} 실패: {e}")
            page_results.append({"page": page_num, "error": str(e), "cached": False})

    # 5) 응답
    if total_pages == 1:
        # 단일 페이지인 경우 간단한 응답
        return {
            "message": f"{book_title} 음원 생성 완료",
            "page": 1,
            "chunks": page_results[0].get("chunks", 0),
            "duration": page_results[0].get("duration", 0),  # 실제 음악 길이
            "book_id": book_id,
            "cached": page_results[0].get("cached", False),
        }
    else:
        # 여러 페이지인 경우 상세 응답
        return {
            "message": f"{book_title} 총 {total_pages} 페이지 처리 완료",
            "book_id": book_id,
            "total_pages": total_pages,
            "text_length": len(text),
            "pages": page_results,
        }




















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
