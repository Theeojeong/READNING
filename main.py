from fastapi import FastAPI
from fastapi.responses import FileResponse
from routers import musicgen_upload_router
from config import OUTPUT_DIR, FINAL_MIX_NAME
import os

app = FastAPI(title="Readning API", version="1.0") #FastAPI 서버 호출

app.include_router(musicgen_upload_router.router)

@app.get("/")  # root 엔드포인트 , 서버 상태 체크 , 홈페이지 역할의 간단 JSON역할
def root():
    return { "message": "Readning API is running" }

@app.get("/download")
def download_final_mix():
    path = os.path.join(OUTPUT_DIR, FINAL_MIX_NAME)
    if os.path.exists(path):
        return FileResponse(path, filename = FINAL_MIX_NAME, media_type="audio/wav")
    return {"error" : "최종 음원이 존재하지 않습니다."}