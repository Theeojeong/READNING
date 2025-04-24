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


    musicgen_service.generate_music_samples(global_prompt = global_prompt, regional_prompts = regional_prompts)
    
    output_filename = f"ch{page}.wav"

    merge_service.build_and_merge_clips_with_repetition(
        text_chunks=chunks,
        clip_dir=OUTPUT_DIR,
        output_name=output_filename,
        clip_duration=GEN_DURATION,
        total_duration=TOTAL_DURATION,
        fade_ms=1500
    )

    return {
       "message": "Music generated",
        "download_url": f"/{OUTPUT_DIR}/{book_id}/ch{page}.wav"
    }


# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------

# @router.post("/music-v2")

# def generate_music_from_upload_v2(
#     file: UploadFile = File(...),
#     book_id: str = Form(...),
#     page: int = Form(...)
# ):
#     try:
#         # 1) 업로드된 텍스트 파일 읽기
#         text_bytes = file.file.read()
#         if not text_bytes:
#             raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있거나 읽을 수 없습니다.")
#         text = text_bytes.decode("utf-8")

#         # (선택) 원본 텍스트를 기록용으로 저장
#         save_text_to_file(os.path.join(OUTPUT_DIR, "uploaded", f"{book_id}_ch{page}.txt"), text)

#         # # 2) 긴 글을 여러 세그먼트로 분할 (GPT 토큰 한계 대비)
#         # segments = list(split_text.split_text_into_processing_segments(text))
#         # if not segments or not isinstance(segments, list):
#         #     raise HTTPException(status_code=500, detail="텍스트 세그먼트화 실패")

#         # # 3) 각 세그먼트를 GPT로 분석해 감정 전환점 찾기
#         # turning_points = []
#         # offset = 0
#         # for segment in segments:
#         #     seg_points = analyze_emotions_with_gpt.analyze_emotions_with_gpt(segment)
#         #     if seg_points:
#         #         for point in seg_points:
#         #             # 세그먼트 내부 위치 → 전체 텍스트 절대 위치로 변환
#         #             turning_points.append(point + offset)
#         #     offset += len(segment)

#         # 중복 제거 및 정렬
#         # turning_points = sorted(set(turning_points))

#         # 4) 전환점을 기준으로 다시 텍스트를 ‘감정 청크’로 분할
#         chunks = chunk_text_by_emotion.chunk_text_by_emotion(text)
#         if not chunks or not isinstance(chunks, list):
#             raise HTTPException(status_code=500, detail="감정 기반 청킹 실패")

#         # 5) 각 청크에 대해 MusicGen용 프롬프트 생성
#         music_prompts = []
#         for chunk_text in chunks:
#             prompt = prompt_service.generate_regional(chunk_text)
#             music_prompts.append(prompt)
#         if not music_prompts:
#             raise HTTPException(status_code=500, detail="프롬프트 생성 실패")

#         # 6) MusicGen 호출 (글로벌 프롬프트 + 청크별 프롬프트)
#         global_prompt = prompt_service.generate_global(text)
#         musicgen_service.generate_music_samples(
#             global_prompt=global_prompt,
#             regional_prompts=music_prompts
#         )

#         # 7) 생성된 클립들을 병합해 최종 WAV 만들기
#         output_filename = f"ch{page}.wav"
#         book_output_dir = os.path.join(OUTPUT_DIR, book_id)
#         ensure_dir(book_output_dir)

#         merge_service.build_and_merge_clips_with_repetition(
#             text_chunks=chunks,
#             clip_dir=OUTPUT_DIR,                       # 개별 클립 저장 위치
#             output_name=f"{book_id}/{output_filename}",# 최종 파일 경로
#             clip_duration=GEN_DURATION,
#             total_duration=TOTAL_DURATION,
#             fade_ms=1500
#         )

#         # 8) 성공 응답(JSON) 반환
#         return {
#             "message": "Music generated (v2)",
#             "download_url": f"/{OUTPUT_DIR}/{book_id}/{output_filename}"
#         }

#     except Exception as e:
#         # 디버깅용 로그 출력
#         print(f"❌ music-v2 처리 중 오류: {e}")
#         # 클라이언트에게 500 에러 JSON 반환
#         raise HTTPException(status_code=500, detail="음악 생성 중 오류가 발생했습니다.")

# ---------------------------------------------------------------------------------------------------------
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
            regional_prompts=music_prompts
        )

        # 5) WAV 병합
        output_filename = f"ch{page}.wav"
        ensure_dir(os.path.join(OUTPUT_DIR, book_id))
        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            clip_dir=OUTPUT_DIR,
            output_name=f"{book_id}/{output_filename}",
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