@REM ##uvicorn main:app --reload

@REM 외부사용자 전용 
uvicorn main:app --host 0.0.0.0 --port 8000 
