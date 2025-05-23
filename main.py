from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware ##프론트와 연결 위한 CORS설정 
from routers import musicgen_upload_router
from config import OUTPUT_DIR, FINAL_MIX_NAME
from utils.file_utils import secure_filename
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

@app.get("/")  # root 엔드포인트 , 서버 상태 체크 , 홈페이지 역할의 간단 JSON역할
def root():
    return { "message": "Readning API is running" }



@app.get("/gen_musics/{user_id}/{book_title}/ch{page}.wav")
def download_music(user_id: str, book_title: str, page: int):
    safe_title = secure_filename(book_title)
    file_path  = os.path.join(OUTPUT_DIR, user_id, safe_title, f"ch{page}.wav")

    # 👉  파일이 없으면 404 로 돌려주기
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 👉  있을 때는 audio/wav 로 확실하게 응답
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=f"ch{page}.wav",
        headers={"Content-Disposition": f'inline; filename="ch{page}.wav"'},
    )