import os
import requests
from typing import List
from config import OUTPUT_DIR
from utils.file_utils import ensure_dir
from services.model_manager import musicgen_manager

def generate_music_samples(
    global_prompt: str,
    regional_prompts: list,
    relative_output_dir: str,
) -> List[str]:
    """
    Replicate API를 사용해 오디오 파일을 생성합니다.
    - meta/musicgen 모델을 사용합니다.
    - 각 프롬프트에 대해 병렬 또는 순차적으로 API를 호출하여 음악을 생성합니다.
    """
    base_output_dir = OUTPUT_DIR

    # 기본 출력 디렉토리 및 대상 책/청크 디렉토리 보장
    if not os.path.exists(base_output_dir):
        ensure_dir(OUTPUT_DIR)
    target_dir = os.path.join(base_output_dir, relative_output_dir)
    ensure_dir(target_dir)
    
    print("🚀 Replicate API를 사용하여 음악 생성 시작...")
    saved_paths: List[str] = []
    
    # Replicate 클라이언트 가져오기
    client = musicgen_manager.client
    if not client:
        raise RuntimeError("Replicate 클라이언트가 초기화되지 않았습니다.")

    # 각 프롬프트에 대해 음악 생성
    for i, prompt in enumerate(regional_prompts):
        print(f"[Replicate] Generating chunk {i+1}/{len(regional_prompts)}: {prompt[:30]}...")
        
        try:
            # Replicate API 호출
            # meta/musicgen 모델 사용
            output = client.run(
                "meta/musicgen:671ac9046605671320a8808632f121b23a277517622863a95cd733231b10baf5",
                input={
                    "prompt": prompt,
                    "model_version": "melody",
                    "duration": 30  # 30초 생성
                }
            )
            
            # output은 오디오 파일 URL임
            audio_url = output
            print(f"   -> Generated URL: {audio_url}")
            
            # 파일 다운로드 및 저장
            filename = f"regional_output_{i+1}.wav"
            save_path = os.path.join(target_dir, filename)
            
            response = requests.get(audio_url)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                saved_paths.append(save_path)
                print(f"   -> Saved to: {save_path}")
            else:
                print(f"❌ Failed to download audio: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Replicate generation failed for chunk {i+1}: {e}")
            # 실패 시에도 계속 진행하거나 예외 처리
            continue

    return saved_paths
