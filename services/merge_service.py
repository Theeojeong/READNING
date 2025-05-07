from pydub import AudioSegment
import os
from typing import List
from utils.file_utils import delete_files_in_directory


def build_and_merge_clips_with_repetition(
        text_chunks : list[str],
        base_output_dir : str,
        book_id_dir : str,
        output_name : str,
        clip_duration : int ,
        total_duration : int ,
        fade_ms : int = 1500,
        cleanup_regionals: bool = False # 인자 추가
) -> str:
    print("Muerging clips...")

    lengths = [len(t) for t in text_chunks]
    min_len = min(lengths)

    raw_repeats = [max(1, round(l / min_len)) for l in lengths]
    total_clips = sum(raw_repeats)
    max_clips = total_duration // clip_duration

    if total_clips > max_clips:
        scale = max_clips / total_clips
        raw_repeats = [max(1, round(r * scale)) for r in raw_repeats]
    
    full_track = AudioSegment.silent(duration=0)

    for i, repeat_count in enumerate(raw_repeats):
        clip_path = os.path.join(base_output_dir, book_id_dir, f"regional_output_{i+1}.wav")
        if not os.path.exists(clip_path):
            print(f"⚠️ {clip_path} not found, skipping.")
            continue

        clip = AudioSegment.from_wav(clip_path)

        for _ in range(repeat_count):
            if len(full_track) > 0:
                full_track = full_track.append(clip, crossfade=fade_ms)
            else:
                full_track += clip.fade_in(fade_ms)

    output_path = os.path.join(base_output_dir, book_id_dir, output_name)
    full_track.export(output_path, format="wav")

    clip_dir_path = os.path.join(base_output_dir, book_id_dir)
    # delete_files_in_directory(clip_dir_path, extension=".wav", exclude_files=[output_name])

    if cleanup_regionals:           # ★ 선택적으로 지움
        delete_files_in_directory(
            clip_dir_path,
            extension=".wav",
            exclude_files=[output_name]
        )

    # ✅ 완료 로그 추가
    print(f"[✓] Merging finished → {output_path}")

    return output_path
