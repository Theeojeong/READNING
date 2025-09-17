from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware ##프론트와 연결 위한 CORS설정 
from routers import musicgen_upload_router
from config import OUTPUT_DIR, FINAL_MIX_NAME
from utils.file_utils import secure_filename
from pathlib import Path
import os

app = FastAPI(title="Readning API", version="1.0") #FastAPI 서버 호출

#  origins = [
#     " 페이지 도메인 ",
#     " 프론트 페이지 도메인 ",
#     - 등 -
#     ]

# # 프론트에서 접근하는 모든 도메인 허용. 개발자에 따라 특정 출처만 허용할 수 있음.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용) / 보안 강화 시 도메인 지정
    allow_credentials=False,
    allow_methods=["*"],  # GET, POST 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


app.include_router(musicgen_upload_router.router)

@app.get("/")
def health_check():
    return {"message": "Readning API is running"}


@app.get("/gen_musics/{user_id}/{book_title}/ch{page}.wav")
def download_music(user_id: str, book_title: str, page: int):
    safe_title = secure_filename(book_title)
    path = Path(OUTPUT_DIR) / user_id / safe_title / f"ch{page}.wav"

    if not path.exists():
        raise HTTPException(404, "file not found")

    return FileResponse(
        path, media_type="audio/wav",
        filename=f"ch{page}.wav",
        headers={"Content-Disposition": f'inline; filename="ch{page}.wav"'}
    )

# ───────────────────────────────────────────────────────────────
# ② 레거시 구조: /gen_musics/<book_title>/ch{page}.wav
# ───────────────────────────────────────────────────────────────
@app.get("/gen_musics/{book_title}/ch{page}.wav", include_in_schema=False)
def legacy_download(book_title: str, page: int):
    path = Path(OUTPUT_DIR) / book_title / f"ch{page}.wav"
    if not path.exists():
        raise HTTPException(404, "file not found (legacy)")
    return FileResponse(path, media_type="audio/wav")