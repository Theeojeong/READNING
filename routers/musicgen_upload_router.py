from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services import analyze_emotions_with_gpt, chunk_text_by_emotion, prompt_service, musicgen_service, emotion_service, merge_service, split_text
from utils.file_utils import save_text_to_file, ensure_dir
import os
from config import OUTPUT_DIR, FINAL_MIX_NAME, GEN_DURATION, TOTAL_DURATION


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
