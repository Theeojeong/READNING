from audiocraft.data.audio import audio_write
import os
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
    MusicGen을 사용해 오디오 파일을 생성합니다.
    - global_prompt로 초기 멜로디를 만들고,
    - regional_prompts를 순서대로 적용하며 변주를 생성합니다.
    - 각 변주는 'regional_output_{i}.wav'로 저장됩니다.
    반환값: 저장된 오디오 파일의 전체 경로 리스트
    """
    base_output_dir = OUTPUT_DIR

    # 기본 출력 디렉토리 및 대상 책/청크 디렉토리 보장
    if not os.path.exists(base_output_dir):
        ensure_dir(OUTPUT_DIR)
    target_dir = os.path.join(base_output_dir, relative_output_dir)
    ensure_dir(target_dir)
    
    print("Loading MusicGen model...")
    model = musicgen_manager.get_model()
    sample_rate = musicgen_manager.sample_rate
    
    print("[1] Generating global melody...")
    base_wav = model.generate([global_prompt])[0]

    # iterative refine
    melody = base_wav
    saved_paths: List[str] = []
    for i, prompt in enumerate(regional_prompts):
        print(f"[2] Generating regional variation {i+1}/{len(regional_prompts)}")
        wav = model.generate_with_chroma([prompt], melody, sample_rate)[0]
        # Update melody to pass to next chunk
        melody = wav

        # Save & Listen
        filename = f"regional_output_{i+1}"
        path_no_ext = os.path.join(base_output_dir, relative_output_dir, filename)
        audio_write(path_no_ext, wav.cpu(), sample_rate, strategy="loudness", loudness_compressor=True)
        saved_paths.append(f"{path_no_ext}.wav")

    return saved_paths
