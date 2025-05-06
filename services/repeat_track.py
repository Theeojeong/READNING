# services/repeat_track.py
from pydub import AudioSegment
import os, math

def repeat_clips_to_length(
    folder: str,                 # ex) gen_musics/string/ch01
    base_name: str,              # ex) regional_output_
    clip_duration: int = 30,     # sec
    target_sec: int = 240,       # sec
    crossfade_ms: int = 1500,
    output_name: str = "final_mix.wav",
):
    """
    folder / base_name{i+1}.wav 파일들을
    A→A→A→B→B→B 식으로 반복해 target_sec 길이로 만듭니다.
    """
    clips = []
    idx = 1
    while True:
        path = os.path.join(folder, f"{base_name}{idx}.wav")
        if not os.path.exists(path):
            break
        clips.append(AudioSegment.from_wav(path))
        idx += 1

    if not clips:
        raise FileNotFoundError("No regional_output_*.wav found")

    repeats = math.ceil(target_sec / (len(clips) * clip_duration))
    print(f"[repeat_track] repeats per clip = {repeats}")

    track = AudioSegment.silent(0)
    for clip in clips:
        for _ in range(repeats):
            track = track.append(clip, crossfade=crossfade_ms)

    track = track[: target_sec * 1000]  # 딱 맞춰 자르기
    out_path = os.path.join(folder, output_name)
    track.export(out_path, "wav")
    print(f"[✓] Repeated mix → {target_sec}s : {out_path}")
    return out_path