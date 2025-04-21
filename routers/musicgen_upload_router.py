from fastapi import APIRouter, UploadFile, File
from services import prompt_service, musicgen_service, emotion_service, merge_service
from utils.file_utils import save_text_to_file
import os
from config import OUTPUT_DIR, FINAL_MIX_NAME, GEN_DURATION, TOTAL_DURATION


router = APIRouter(prefix="/generate", tags = ["UploadWorkflow"])

@router.post("/music")

def generate_music_from_upload(file : UploadFile = File (...)):
    text = file.file.read().decode("utf-8") #사용자로부터 text파일 

    save_text_to_file(os.path.join(OUTPUT_DIR,"uploaded"),text)

    global_prompt = prompt_service.generate_global(text)
    chunks = emotion_service.hybrid_chunk_text_by_emotion_fulltext(text)

    regional_prompts = []
    for i, chunk_text in enumerate(chunks):
        rprompt = prompt_service.generate_regional(chunk_text)
        musicgen_prompt = prompt_service.compose_musicgen_prompt(global_prompt, rprompt)
        regional_prompts.append(musicgen_prompt)


    musicgen_service.generate_music_samples(global_prompt = global_prompt, regional_prompts = regional_prompts)

    merge_service.build_and_merge_clips_with_repetition(
        text_chunks=chunks,
        clip_dir=OUTPUT_DIR,
        output_name=FINAL_MIX_NAME,
        clip_duration=GEN_DURATION,
        total_duration=TOTAL_DURATION,
        fade_ms=1500
    )

    return {"message": "Music generated", "download_url": "/download"}