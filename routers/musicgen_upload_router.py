from fastapi import APIRouter, Form, HTTPException

from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
    merge_service,
)

from utils.file_utils import save_text_to_file, ensure_dir
import os
from config import OUTPUT_DIR, GEN_DURATION, TOTAL_DURATION


router = APIRouter(prefix="/generate", tags=["UploadWorkflow"])


@router.post("/music-by-chapter", summary="단일 챕터 텍스트로 음악 생성")
async def generate_music_by_chapter(
    book_id: str        = Form(...),
    chapter_index: int  = Form(..., ge=0),
    chapter_title: str  = Form("") ,
    text: str           = Form(...),
    target_len: int     = Form(TOTAL_DURATION),
):
    """
    단일 챕터 텍스트를 입력으로 받아 해당 챕터의 배경 음악을 생성합니다.

    요청 필드(form-data)
    - book_id: 책 식별자(문자열)
    - chapter_index: 챕터 인덱스(0부터 시작, 정수)
    - chapter_title: 챕터 제목(선택)
    - text: 챕터 원문 텍스트(문자열, 필수)
    - target_len: 결과 음원 길이(초). 기본값은 TOTAL_DURATION

    처리 개요
    1) 입력 검증 후 작업 디렉터리 생성(요청별 고유 폴더) → 병렬 실행 시 충돌 방지
    2) 챕터 텍스트를 그대로 저장(재현/디버깅 용도)
    3) 감정 전환점 탐색 → 감정 단위 청크 분리
    4) 글로벌/리저널 프롬프트 생성 후 청크 개수만큼 regional 트랙 생성
    5) 작업 폴더 내에서 트랙들을 병합하여 챕터 단일 음원 생성
    6) 최종 파일을 프론트가 기대하는 고정 경로(gen_musics/{book_id}/ch{chapter_index}.wav)로 원자적 이동

    결과
    - download_url: "/gen_musics/{book_id}/ch{chapter_index}.wav"
    - chapter_index, chapter_title 함께 반환

    오류 처리
    - 400: text 비어 있음, target_len ≤ 0
    - 500: 감정 청크 분리/음악 생성/병합 중 내부 오류
    """

    # 1) 입력값 검증 --------------------------------------------------
    if not text.strip():
        raise HTTPException(400, "챕터 텍스트가 비어 있습니다")
    if target_len <= 0:
        raise HTTPException(400, "target_len 은 0보다 커야 합니다")

    # 2) 출력 루트 디렉터리 보장: gen_musics/{book_id}
    ensure_dir(os.path.join(OUTPUT_DIR, book_id))

    # 3) 병렬 안전성을 위한 고유 작업 디렉터리 생성
    #    예) gen_musics/{book_id}/ch{idx}__{timestamp}/
    import time
    work_dir_rel = os.path.join(book_id, f"ch{chapter_index}__{int(time.time()*1000)}")
    work_dir_abs = os.path.join(OUTPUT_DIR, work_dir_rel)
    ensure_dir(work_dir_abs)

    # 4) 재현 가능성 확보를 위해 입력 텍스트 보존
    chapter_txt_path = os.path.join(work_dir_abs, f"ch{chapter_index}.txt")
    tmp_path         = os.path.join(work_dir_abs, f"ch{chapter_index}_tmp.txt")
    save_text_to_file(chapter_txt_path, text)
    save_text_to_file(tmp_path, text)

    # 5) 감정 전환점 기반 청크 분리
    try:
        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)
    except Exception as e:
        print("[music-by-chapter] chunking error:", e)
        raise HTTPException(500, "텍스트 청크 분할 중 오류가 발생했습니다")

    # 6) 프롬프트 생성 및 regional 샘플 생성
    try:
        global_prompt = prompt_service.generate_global(text)
        regional_prompts = []
        for chunk in chunks:
            chunk_text = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            regional = prompt_service.generate_regional(chunk_text)
            regional_prompts.append(
                prompt_service.compose_musicgen_prompt(global_prompt, regional)
            )

        #   생성된 regional 트랙은 작업 디렉터리(work_dir_rel)에 저장
        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=regional_prompts,
            book_id_dir=work_dir_rel,
        )
    except Exception as e:
        print("[music-by-chapter] musicgen error:", e)
        raise HTTPException(500, "음악 생성 중 오류가 발생했습니다")

    # 7) 챕터 단일 음원으로 병합
    output_name = f"ch{chapter_index}.wav"
    try:
        #   병합은 작업 디렉터리 내부에서 수행
        merged_path = merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir=work_dir_rel,
            output_name=output_name,
            clip_duration=GEN_DURATION,
            total_duration=target_len,
            fade_ms=1500,
        )
        # 8) 최종 파일을 프론트가 기대하는 고정 경로로 이동(원자적 교체 우선)
        final_out = os.path.join(OUTPUT_DIR, book_id, output_name)
        try:
            # 가능하면 os.replace로 원자적 이동
            os.replace(merged_path, final_out)
        except Exception:
            # 일부 파일시스템에서 실패 시 복사로 대체
            import shutil
            shutil.copyfile(merged_path, final_out)
    except Exception as e:
        print("[music-by-chapter] merge error:", e)
        raise HTTPException(500, "오디오 병합 중 오류가 발생했습니다")

    return {
        "message": f"챕터 {chapter_index} 음원 생성 완료",
        "download_url": f"/{OUTPUT_DIR}/{book_id}/{output_name}",
        "chapter_index": chapter_index,
        "chapter_title": chapter_title,
    }
