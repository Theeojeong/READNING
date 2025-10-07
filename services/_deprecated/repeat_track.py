# services/repeat_track.py
import os, math
from pathlib import Path
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)
print("[repeat_track] loaded from", __file__)

def repeat_clips_to_length(
    folder: str,
    base_name: str = "regional_output_",
    clip_duration: int | None = None,   # sec, None 이면 자동 계산
    target_sec: int = 240,
    crossfade_ms: int = 1500,
    output_name: str = "final_mix.wav",
):

    # ① 클립 로딩 ------------------------------------------------------
    clips: list[AudioSegment] = []
    for idx in range(1, 9999):
        p = os.path.join(folder, f"{base_name}{idx}.wav")
        if not os.path.exists(p):
            break
        c = AudioSegment.from_wav(p)
        d = len(c)
        print(f"[repeat_track] {p} → {d} ms")
        if d == 0:
            logger.warning(f"[repeat_track] skip empty clip {p}")
            continue
        clips.append(c)

    if not clips:
        raise FileNotFoundError("No usable regional_output_*.wav found")

    # ② clip_duration 자동 결정 ---------------------------------------
    if not clip_duration or clip_duration <= 0:
        clip_duration = len(clips[0]) // 1000 or 1   # 1초 이상 보장
        logger.warning(f"[repeat_track] clip_duration auto-set to {clip_duration}s")

    # ③ 반복 횟수 계산 --------------------------------------------------
    repeats = math.ceil(target_sec / (len(clips) * clip_duration))
    logger.info(f"[repeat_track] repeats per clip = {repeats}")

    # ④ 클립 반복 & crossfade 보정 -------------------------------------
    track = AudioSegment.silent(duration=0)
    for clip in clips:
        dur = len(clip)
        cf  = crossfade_ms if crossfade_ms < dur else max(0, dur // 4)
        for _ in range(repeats):
            track = track.append(clip, crossfade=(0 if len(track) == 0 else cf))

    # ⑤ 자르기 & 저장 --------------------------------------------------
    track = track[:target_sec * 1000]
    out_path = os.path.join(folder, output_name)
    track.export(out_path, "wav")
    logger.info(f"[repeat_track] saved {out_path} ({len(track)} ms)")
    return out_path
