# ollama_run.py
import subprocess, time, os, signal

# ── 1) 환경변수에 GPU 사용 지시 --─────────────
env = os.environ.copy()
env["OLLAMA_ACCEL"] = "gpu"        # "cpu" 로 바꾸면 CPU 강제

# ── 2) 백그라운드로 ollama serve 실행 ────────
proc = subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,     # 로그 버리거나 파일로 리다이렉트
    stderr=subprocess.STDOUT,
    preexec_fn=os.setsid,          # 부모 종료 후에도 살아 있게(Linux)
    env=env                        # ★ 수정: env 전달
)

time.sleep(5)                      # 서버 기동 대기
print("Ollama server launched with PID:", proc.pid)