from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from services.ebooks2text import split_txt_into_pages, convert_and_split
from services import (
    chunk_text_by_emotion,
    prompt_service,
    musicgen_service,
    merge_service,
    firestore_service,
)

from utils.file_utils import save_text_to_file, ensure_dir, secure_filename
import json
import os
from config import OUTPUT_DIR, FINAL_MIX_NAME, GEN_DURATION, TOTAL_DURATION
from typing import List
from pathlib import Path 
from services.repeat_track import repeat_clips_to_length


router = APIRouter(prefix="/generate", tags = ["UploadWorkflow"])

@router.post("/music")

def generate_music_from_upload(
    file : UploadFile = File (...),
    book_id: str = Form(...),
    page: int = Form(...)
    ):
    # 안전한 텍스트 디코딩
    try:
        text = file.file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            file.file.seek(0)
            text = file.file.read().decode("cp949")
        except UnicodeDecodeError:
            file.file.seek(0)
            text = file.file.read().decode("latin1")
    
    if not text.strip():
        raise HTTPException(400, "업로드된 파일이 비어 있습니다.") 

    save_text_to_file(os.path.join(OUTPUT_DIR,"uploaded",f"{book_id}_ch{page}.txt"), text)

    global_prompt = prompt_service.generate_global(text)
    chunks = chunk_text_by_emotion.chunk_text_by_emotion(text)

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
    page: int = Form(1),
):
    """페이지를 분할한 뒤 해당 페이지를 감정 단위로 나눠 음악을 생성한다."""

    # ── 1) 텍스트 읽기 및 페이지 분할 ────────────────────────────
    text = file.file.read().decode("utf-8")
    original_stem = Path(file.filename).stem
    if not text:
        raise HTTPException(400, "업로드된 파일이 비어 있습니다.")

    pages = split_txt_into_pages(text)
    if not pages:
        raise HTTPException(400, "페이지 분할에 실패했습니다")

    warning = None
    if page < 1 or page > len(pages):
        warning = (
            f"page 값은 1~{len(pages)} 사이여야 합니다. "
            "기본값 1로 처리합니다."
        )
        print(f"[!] {warning}")
        page = 1

    page_text = pages[page - 1]

    # ★ 챕터 전용 하위 폴더 경로
    chapter_dir = f"{book_id}/{original_stem}"
    ensure_dir(os.path.join(OUTPUT_DIR, chapter_dir))

    uploaded_path = os.path.join(
        OUTPUT_DIR, "uploaded", f"{chapter_dir}_p{page}.txt")
    save_text_to_file(uploaded_path, page_text)

    tmp_path = os.path.join(
        OUTPUT_DIR, "uploaded", f"{chapter_dir}_tmp.txt")
    save_text_to_file(tmp_path, page_text)

    # ── 2) preference 파싱 ───────────────────────────────────────
    try:
        pref_list: List[str] = json.loads(preference)
        if not isinstance(pref_list, list):
            raise ValueError
    except Exception:
        print("[!] preference 파싱 실패: 기본값 [] 사용")
        pref_list = []

    # ── 3) 감정-청크 분할 ─────────────────────────────────────────
    chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)
    print(f"청크 개수: {len(chunks)}")

    # ── 4) 프롬프트 생성 (취향 반영) ───────────────────────────────
    global_prompt = prompt_service.generate_global(page_text)
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
        book_id_dir=chapter_dir,
    )

    # ── 6) WAV 병합 ──────────────────────────────────────────────
    # ensure_dir(os.path.join(OUTPUT_DIR, book_id))
    # output_filename = FINAL_MIX_NAME  # config.py 의 "final_mix.wav"
    ensure_dir(os.path.join(OUTPUT_DIR, book_id))
    output_filename = f"ch{page}.wav"

    merge_service.build_and_merge_clips_with_repetition(
        text_chunks=chunks,
        base_output_dir=OUTPUT_DIR,
        book_id_dir=chapter_dir,
        output_name=output_filename,
        clip_duration=GEN_DURATION,
        total_duration=TOTAL_DURATION,
        fade_ms=1500,
    )

    response = {
        "message": "Music generated (v3)",
        "download_url": f"/{OUTPUT_DIR}/{chapter_dir}/{output_filename}",
    }
    if warning:
        response["warning"] = warning
    return response


def get_output_path(user_id: str, book_dir: str, chapter: int) -> str:
    return os.path.join(OUTPUT_DIR, user_id, book_dir, f"ch{chapter}.wav")

@router.post("/music-v3-long", summary="Generate long BGM for one page")
async def generate_music_long(
    file: UploadFile = File(...),
    user_id: str     = Form(...),
    book_title: str  = Form(...),
    page: int        = Form(..., ge=0),
    preference: str  = Form("[]"),
    target_len: int  = Form(240),
):

    # ➊ 이미 생성된 파일이 있으면 바로 반환해 무한 재생성 차단
    safe_title  = secure_filename(book_title)
    out_wav     = get_output_path(user_id, safe_title, page)
    if os.path.exists(out_wav):
        logger.info(f"[SKIP] {out_wav} already exists – returning cached file")
        return FileResponse(out_wav, media_type="audio/wav")

    # 1) 텍스트 읽기 --------------------------------------------------
    text = file.file.read().decode("utf-8")
    if not text:
        raise HTTPException(400, "업로드된 파일이 비어 있습니다.")
    if target_len <= 0:
        raise HTTPException(400, "target_len 은 0보다 커야 합니다")

    # 2) 저장 경로 ----------------------------------------------------
    # safe_title  = secure_filename(book_title)
    book_dir    = os.path.join(user_id, safe_title)      # uid/책제목
    abs_bookdir = os.path.join(OUTPUT_DIR, book_dir)
    ensure_dir(abs_bookdir)

    save_text_to_file(os.path.join(abs_bookdir, f"ch{page}.txt"), text)
    tmp_path = os.path.join(abs_bookdir, f"ch{page}_tmp.txt")
    save_text_to_file(tmp_path, text)

    # 3) preference 파싱 --------------------------------------------
    try:
        pref_list: List[str] = json.loads(preference)
        if not isinstance(pref_list, list):
            raise ValueError
    except Exception:
        raise HTTPException(400, "preference 는 JSON 배열 형식이어야 합니다")

    # 4) 청크 분할 ----------------------------------------------------
    try:
        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)
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
            pref_line = f"User preference: {', '.join(pref_list)}" if pref_list else ""
            rp.append(prompt_service.compose_musicgen_prompt(
                global_prompt, f"{regional}\n{pref_line}"
            ))
        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=rp,
            book_id_dir=book_dir,
        )
    except Exception as e:
        print("[music-v3-long] musicgen error:", e)
        raise HTTPException(500, "음악 생성 중 오류가 발생했습니다")

    # 6) 병합 및 반복 -------------------------------------------------
    output_filename = f"ch{page}.wav"
    try:
        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir=book_dir,
            output_name=output_filename,
            clip_duration=GEN_DURATION,
            total_duration=target_len,
            fade_ms=1500,
        )
        repeat_clips_to_length(
            folder=abs_bookdir,
            base_name="regional_output_",
            clip_duration=GEN_DURATION // 1000,
            target_sec=target_len,
            crossfade_ms=1000,
            output_name=output_filename,
        )
    except Exception as e:
        print("[music-v3-long] merge/repeat error:", e)
        raise HTTPException(500, "오디오 병합 또는 반복 처리 중 오류가 발생했습니다")

    # 7) 응답 --------------------------------------------------------
    return {
        "message": f"{safe_title} p{page} 음원 생성 완료",
        "download_url": f"/{OUTPUT_DIR}/{user_id}/{safe_title}/{output_filename}",
        "page": page,
    }


@router.post("/music-pages")
async def generate_music_for_pages(
    file: UploadFile = File(...),
    book_id: str = Form(...),
):
    """Generate music for each page of a text file."""

    # 1) read the uploaded text
    text = file.file.read().decode("utf-8")
    if not text:
        raise HTTPException(400, "업로드된 파일이 비어 있습니다.")

    # 2) split into page texts
    pages = split_txt_into_pages(text)
    if not pages:
        raise HTTPException(400, "페이지를 분할하지 못했습니다")

    download_urls: List[str] = []

    for idx, page_text in enumerate(pages, start=1):
        # 저장용 파일 경로 (원본 및 임시)
        uploaded_path = os.path.join(OUTPUT_DIR, "uploaded", f"{book_id}_ch{idx}.txt")
        tmp_path = os.path.join(OUTPUT_DIR, "uploaded", f"{book_id}_tmp.txt")
        save_text_to_file(uploaded_path, page_text)
        save_text_to_file(tmp_path, page_text)

        # 감정 기반 청크 분할
        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)

        # 프롬프트 준비
        global_prompt = prompt_service.generate_global(page_text)
        music_prompts = []
        for chunk in chunks:
            chunk_txt = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            regional = prompt_service.generate_regional(chunk_txt)
            music_prompts.append(
                prompt_service.compose_musicgen_prompt(global_prompt, regional)
            )

        # MusicGen 생성
        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=music_prompts,
            book_id_dir=book_id,
        )

        # 결과 병합
        output_filename = f"ch{idx}.wav"
        ensure_dir(os.path.join(OUTPUT_DIR, book_id))
        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir=book_id,
            output_name=output_filename,
            clip_duration=GEN_DURATION,
            total_duration=TOTAL_DURATION,
            fade_ms=1500,
        )

        download_urls.append(f"/{OUTPUT_DIR}/{book_id}/{output_filename}")

    return {"message": "Music generated for pages", "download_urls": download_urls}


@router.post("/music-ebook")
async def generate_music_for_ebook(
    file: UploadFile = File(...),
    book_id: str = Form(...),
    preference: str = Form("[]"),
):
    """Generate music chapter by chapter from a PDF or EPUB file."""

    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".epub", ".txt"]:
        raise HTTPException(400, "Only .pdf, .epub or .txt files are supported")

    ensure_dir(os.path.join(OUTPUT_DIR, "uploaded"))
    upload_path = os.path.join(
        OUTPUT_DIR,
        "uploaded",
        secure_filename(file.filename),
    )
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    if ext in [".pdf", ".epub"]:
        chapters = convert_and_split(upload_path)
    else:
        text = open(upload_path, "r", encoding="utf-8").read()
        pages = split_txt_into_pages(text)
        chapters = [
            {"title": f"Page {i+1}", "content": p} for i, p in enumerate(pages)
        ]

    if not chapters:
        raise HTTPException(400, "챕터를 분할하지 못했습니다")

    chapter_dir = f"{book_id}/{Path(file.filename).stem}"
    ensure_dir(os.path.join(OUTPUT_DIR, chapter_dir))

    try:
        pref_list: List[str] = json.loads(preference)
        if not isinstance(pref_list, list):
            raise ValueError
    except Exception:
        pref_list = []

    download_urls: List[str] = []

    for idx, chapter in enumerate(chapters, start=1):
        chapter_text = chapter["content"]

        uploaded_txt = os.path.join(
            OUTPUT_DIR, "uploaded", f"{chapter_dir}_ch{idx}.txt"
        )
        tmp_path = os.path.join(
            OUTPUT_DIR, "uploaded", f"{chapter_dir}_tmp.txt"
        )
        save_text_to_file(uploaded_txt, chapter_text)
        save_text_to_file(tmp_path, chapter_text)

        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)

        global_prompt = prompt_service.generate_global(chapter_text)
        music_prompts = []
        for chunk in chunks:
            chunk_txt = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            regional = prompt_service.generate_regional(chunk_txt)
            pref_line = (
                f"User preference: {', '.join(pref_list)}" if pref_list else ""
            )
            music_prompts.append(
                prompt_service.compose_musicgen_prompt(
                    global_prompt, f"{regional}\n{pref_line}"
                )
            )

        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=music_prompts,
            book_id_dir=chapter_dir,
        )

        output_filename = f"ch{idx}.wav"
        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir=chapter_dir,
            output_name=output_filename,
            clip_duration=GEN_DURATION,
            total_duration=TOTAL_DURATION,
            fade_ms=1500,
        )

        download_urls.append(f"/{OUTPUT_DIR}/{chapter_dir}/{output_filename}")

    return {
        "message": "Music generated for ebook chapters",
        "download_urls": download_urls,
    }


@router.post("/book")
async def upload_book(
    file: UploadFile = File(...),
    uid: str = Form(...), 
    book_id: str = Form(...),
    book_title: str = Form(...),
):
    """Upload a book (PDF/EPUB) and generate music for each chapter."""

    ensure_dir(os.path.join(OUTPUT_DIR, "uploaded"))
    upload_path = os.path.join(OUTPUT_DIR, "uploaded", secure_filename(file.filename))
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    chapters = convert_and_split(upload_path)
    if not chapters:
        raise HTTPException(400, "챕터를 분할하지 못했습니다")

    safe_title = secure_filename(book_title)
    # sanitized book title followed by the raw title for readability
    base_book_dir = f"{book_id}/{safe_title}/{book_title}"
    # ensure the new base directory exists before processing chapters
    ensure_dir(os.path.join(OUTPUT_DIR, base_book_dir))

    chapter_results: List[dict] = []

    for idx, chapter in enumerate(chapters, start=1):
        chapter_title = chapter.get("title") or f"Chapter {idx}"
        safe_chapter = secure_filename(chapter_title)
        # folder uses sanitized title segment plus raw chapter title
        chapter_dir = f"{base_book_dir}/{chapter_title}"
        ensure_dir(os.path.join(OUTPUT_DIR, chapter_dir))

        uploaded_txt = os.path.join(
            OUTPUT_DIR, "uploaded", f"{safe_title}_{safe_chapter}.txt"
        )
        tmp_path = os.path.join(
            OUTPUT_DIR, "uploaded", f"{safe_title}_{safe_chapter}_tmp.txt"
        )
        save_text_to_file(uploaded_txt, chapter["content"])
        save_text_to_file(tmp_path, chapter["content"])

        chunks = chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)

        global_prompt = prompt_service.generate_global(chapter["content"])
        music_prompts = []
        for chunk in chunks:
            chunk_txt = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
            regional = prompt_service.generate_regional(chunk_txt)
            music_prompts.append(
                prompt_service.compose_musicgen_prompt(global_prompt, regional)
            )

        musicgen_service.generate_music_samples(
            global_prompt=global_prompt,
            regional_prompts=music_prompts,
            book_id_dir=chapter_dir,
        )

        merge_service.build_and_merge_clips_with_repetition(
            text_chunks=chunks,
            base_output_dir=OUTPUT_DIR,
            book_id_dir=chapter_dir,
            output_name=FINAL_MIX_NAME,
            clip_duration=GEN_DURATION,
            total_duration=TOTAL_DURATION,
            fade_ms=1500,
        )

        music_url = f"/{OUTPUT_DIR}/{chapter_dir}/{FINAL_MIX_NAME}"
        chapter_results.append(
            {
                "title": chapter_title,
                "page": idx,
                "content": chapter["content"],
                "musicUrl": music_url,
            }
        )

    firestore_service.add_book_info(       # ⭐️ ② uid 전달
        uid=uid,
        book_id=book_id,
        data={"title": book_title, "chapters": chapter_results},
    )

    return {
        "uid": uid,
        "book_id": book_id,
        "title": book_title,
        "chapters": chapter_results,
    }


@router.get("/books/{book_id}")
def get_book_info(book_id: str):
    """Retrieve saved book information from Firestore."""
    data = firestore_service.get_book_info(book_id)
    if not data:
        raise HTTPException(status_code=404, detail="Book not found")
    return data

