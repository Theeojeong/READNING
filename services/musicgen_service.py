from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import os
from config import OUTPUT_DIR, GEN_DURATION
from utils.file_utils import ensure_dir

def generate_music_samples(
    global_prompt: str,
    regional_prompts: list,
    book_id_dir:str
    ):
    """
    1) Global prompt로 base melody 생성
    2) 각 regional prompt마다 generate_with_chroma(=melody + prompt)
    3) wav 파일 저장 & Notebook 내 재생
    """
    base_output_dir = OUTPUT_DIR

    if not os.path.exists(base_output_dir):
        ensure_dir(OUTPUT_DIR)
    
    print("Loading MusicGen (facebook/musicgen-melody)...")
    model = MusicGen.get_pretrained('facebook/musicgen-melody')
    model.set_generation_params(duration=GEN_DURATION)  # 곡 길이 10초 (예시)
    sr = model.sample_rate
    
    print("[1] Generating global melody...")
    base_wav = model.generate([global_prompt])[0]

    # iterative refine
    melody = base_wav
    saved_paths = []
    for i, prompt in enumerate(regional_prompts):
        print(f"[2] Generating regional variation {i+1}/{len(regional_prompts)}")
        wav = model.generate_with_chroma([prompt], melody, sr)[0]
        # Update melody to pass to next chunk
        melody = wav

        # Save & Listen
        filename = f"regional_output_{i+1}"
        path = os.path.join(base_output_dir, book_id_dir, filename)
        audio_write(path, wav.cpu(), sr, strategy="loudness", loudness_compressor=True)
        saved_paths.append(f"{path}.wav")

    return saved_paths
