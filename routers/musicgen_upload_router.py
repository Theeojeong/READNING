from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services import analyze_emotions_with_gpt, chunk_text_by_emotion, prompt_service, musicgen_service, emotion_service, merge_service, split_text
from utils.file_utils import save_text_to_file, ensure_dir
import json, os
from config import OUTPUT_DIR, FINAL_MIX_NAME, GEN_DURATION, TOTAL_DURATION
from typing import List
from pathlib import Path 


router = APIRouter(prefix="/generate", tags = ["UploadWorkflow"])

@router.post("/music")

def generate_music_from_upload(
    file : UploadFile = File (...),
    book_id: str = Form(...),
    page: int = Form(...)
    ):
    text = file.file.read().decode("utf-8") #사용자로부터 text파일 

    save_text_to_file(os.path.join(OUTPUT_DIR,"uploaded",f"{book_id}_ch{page}.txt"), text)

    global_prompt = prompt_service.generate_global(text)
    chunks = emotion_service.hybrid_chunk_text_by_emotion_fulltext(text)

    regional_prompts = []
    for i, chunk_text in enumerate(chunks):
        rprompt = prompt_service.generate_regional(chunk_text)
        musicgen_prompt = prompt_service.compose_musicgen_prompt(global_prompt, rprompt)
        regional_prompts.append(musicgen_prompt)


    musicgen_service.generate_music_samples(
        global_prompt = global_prompt,
        regional_prompts = regional_prompts,
        book_id_dir = book_id
        )
    
    output_filename = f"ch{page}.wav"

    merge_service.build_and_merge_clips_with_repetition(
        text_chunks=chunks,
        base_output_dir=OUTPUT_DIR,
        book_id_dir = book_id,
        output_name=output_filename,
        clip_duration=GEN_DURATION,
        total_duration=TOTAL_DURATION,
        fade_ms=1500
    )


    return {
       "message": "Music generated",
        "download_url": f"/{OUTPUT_DIR}/{book_id}/ch{page}.wav"
    }


@router.post("/music-v2")
def generate_music_from_upload_v2(
    file: UploadFile = File(...),
    book_id: str = Form(...),
    page: int = Form(...)
):
    try:
        # 1) 텍스트 읽기
        text = file.file.read().decode("utf-8")
        if not text:
            raise HTTPException(400, "업로드된 파일이 비어 있습니다.")
        save_text_to_file(os.path.join(OUTPUT_DIR,"uploaded",f"{book_id}_ch{page}.txt"), text)

        # 2) 감정-청크 얻기 (임시 파일 경로 넘김)
        tmp_path = os.path.join(OUTPUT_DIR,"uploaded",f"{book_id}_tmp.txt")
        save_text_to_file(tmp_path, text)
        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)

        print(f"청크 개수: {len(chunks)}") 

        # 3) 전역·지역 프롬프트
        global_prompt = prompt_service.generate_global(text)
        music_prompts = []
        for chunk_text in chunks:                    # 튜플 언팩!
            regional = prompt_service.generate_regional(chunk_text)
            music_prompts.append(
                prompt_service.compose_musicgen_prompt(global_prompt, regional)
            )

        # 4) MusicGen 생성
        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=music_prompts,
            book_id_dir = book_id
        )

        # 5) WAV 병합
        output_filename = f"ch{page}.wav"
        ensure_dir(os.path.join(OUTPUT_DIR, book_id))
        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir = book_id,
            output_name=output_filename, # <- 여기 수정함
            clip_duration=GEN_DURATION,
            total_duration=TOTAL_DURATION,
            fade_ms=1500
        )

        return {
            "message": "Music generated (v2)",
            "download_url": f"/{OUTPUT_DIR}/{book_id}/{output_filename}"
        }

    except Exception as e:
        print("❌ music-v2 오류:", e)
        raise HTTPException(500, "음악 생성 중 오류가 발생했습니다.")


@router.post("/music-v3")
async def generate_music_from_upload_v3(
    file: UploadFile = File(...),
    book_id: str = Form(...),
    # 프런트에서 JSON 배열을 문자열로 보내도록 합의
    #   e.g.  ["잔잔한 피아노","자연 소리"]
    preference: str = Form("[]"),
):
    """
    page 파라미터를 없애고 사용자의 음악 취향(preference)을 받는 새 버전.
    preference는 JSON 배열 문자열로 전달받아 List[str]으로 변환해 사용한다.
    """
    # ── 1) 텍스트 읽기 ─────────────────────────────────────────────
    text = file.file.read().decode("utf-8")
    original_stem = Path(file.filename).stem    
    if not text:
        raise HTTPException(400, "업로드된 파일이 비어 있습니다.")

    uploaded_path = os.path.join(OUTPUT_DIR, "uploaded", f"{book_id}.txt")
    save_text_to_file(uploaded_path, text)

    # ── 2) preference 파싱 ───────────────────────────────────────
    try:
        pref_list: List[str] = json.loads(preference)
        if not isinstance(pref_list, list):
            raise ValueError
    except Exception:
        raise HTTPException(400, "preference 는 JSON 배열 형식이어야 합니다")

    # ── 3) 감정-청크 분할 ─────────────────────────────────────────
    tmp_path = os.path.join(OUTPUT_DIR, "uploaded", f"{book_id}_tmp.txt")
    save_text_to_file(tmp_path, text)
    chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)
    print(f"청크 개수: {len(chunks)}")

    # ── 4) 프롬프트 생성 (취향 반영) ───────────────────────────────
    global_prompt = prompt_service.generate_global(text)
    music_prompts = []
    for chunk in chunks:  # chunk 가 튜플이면 (chunk_text, ctx)
        chunk_text = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
        regional = prompt_service.generate_regional(chunk_text)

        # 취향을 한 줄 덧붙여서 compose
        pref_line = f"User preference: {', '.join(pref_list)}" if pref_list else ""
        music_prompts.append(
            prompt_service.compose_musicgen_prompt(
                global_prompt, f"{regional}\n{pref_line}"
            )
        )

    # ── 5) MusicGen 샘플 생성 ────────────────────────────────────
    musicgen_service.generate_music_samples(
        global_prompt=global_prompt,
        regional_prompts=music_prompts,
        book_id_dir=book_id,
    )

    # ── 6) WAV 병합 ──────────────────────────────────────────────
    # ensure_dir(os.path.join(OUTPUT_DIR, book_id))
    # output_filename = FINAL_MIX_NAME  # config.py 의 "final_mix.wav"
    ensure_dir(os.path.join(OUTPUT_DIR, book_id))
    output_filename = f"ch{page}.wav"

    merge_service.build_and_merge_clips_with_repetition(
        text_chunks=chunks,
        base_output_dir=OUTPUT_DIR,
        book_id_dir=book_id,
        output_name=output_filename,
        clip_duration=GEN_DURATION,
        total_duration=TOTAL_DURATION,
        fade_ms=1500,
    )

    return {
        "message": "Music generated (v3)",
        "download_url": f"/{OUTPUT_DIR}/{book_id}/{output_filename}",
    }
