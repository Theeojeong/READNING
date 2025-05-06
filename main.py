from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware ##프론트와 연결 위한 CORS설정 
from routers import musicgen_upload_router
from config import OUTPUT_DIR, FINAL_MIX_NAME
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



@app.get("/gen_musics/{book_id}/ch{page}.wav")
def download_final_mix(book_id: str, page: int):
    filename = f"ch{page}.wav"
    path = os.path.join(OUTPUT_DIR, book_id, filename)

    if os.path.exists(path):
        return FileResponse(path, filename=filename, media_type="audio/wav")
    return {"error": f"최종 음원 파일이 존재하지 않습니다: {path}"}
