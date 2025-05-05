# ollama_run.py
import subprocess, time, os, signal

# 1) 로그 무시하거나 파일에 보냄
proc = subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,         # 로그 버리기
    stderr=subprocess.STDOUT,
    preexec_fn=os.setsid               # 부모 종료 후에도 살아 있게 (Linux)
)

time.sleep(5)                          # 5초만 대기해도 충분
print("Ollama server launched with PID:", proc.pid)
