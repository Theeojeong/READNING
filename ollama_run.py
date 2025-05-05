import subprocess
import time

# Ollama 서버를 백그라운드에서 실행합니다.
# stdout과 stderr는 필요한 경우 캡처할 수 있습니다.
proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 서버가 완전히 시작될 때까지 잠시 대기 (예: 5초)
time.sleep(10)

print("Ollama server launched with PID:", proc.pid)