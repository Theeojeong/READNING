"""
비동기 음악 생성 서비스
각 텍스트 청크에 대해 MusicGen을 호출하고, 생성된 오디오/텍스트 메타데이터를 반환합니다.
복잡한 최적화보다는 이해하기 쉬운 순차 처리 + 명확한 변수명을 사용합니다.
"""

import asyncio
import time
import os
from typing import List, Dict, Any
from services import prompt_service, musicgen_service
from utils.logger import log
from config import GEN_DURATION, OUTPUT_DIR, MAX_CONCURRENT_MUSIC_GENERATION

# MAX_CONCURRENT_MUSIC_GENERATION 값은 config.py에서 관리합니다.


async def process_single_chunk(
    chunk_data: Dict[str, Any],
    chunk_index: int,
    book_relative_dir: str,
    global_prompt: str,
) -> Dict[str, Any]:
    """단일 청크를 처리하여 오디오/텍스트 파일을 생성하고 메타데이터를 반환합니다."""
    start_time = time.time()
    try:
        chunk_text = chunk_data["text"]
        chunk_context = chunk_data.get("context", {})
        
        log(f"🎵 청크 {chunk_index} 음악 생성 시작 (길이: {len(chunk_text)}자)")
        
        # 음악 프롬프트 생성
        regional_prompt = prompt_service.generate_regional(chunk_text)
        music_prompt = prompt_service.compose_musicgen_prompt(global_prompt, regional_prompt)
        
        # 음악 생성 (비동기, 순차 처리)
        audio_url: str = ""
        try:
            saved_paths = await asyncio.get_event_loop().run_in_executor(
                None,
                musicgen_service.generate_music_samples,
                global_prompt,
                [music_prompt],
                f"{book_relative_dir}/chunk_{chunk_index}"
            )
            # 저장된 첫 번째 오디오 파일을 URL로 반환
            if saved_paths and len(saved_paths) > 0:
                audio_path = saved_paths[0]
                audio_url = "/" + audio_path.replace("\\", "/")
            else:
                raise RuntimeError("No audio file generated")
        except Exception as music_error:
            log(f"🎵 청크 {chunk_index} MusicGen 오류: {music_error}")
            # MusicGen 실패 시 더미 파일 생성
            dummy_audio_dir = os.path.join(OUTPUT_DIR, f"{book_relative_dir}/chunk_{chunk_index}")
            os.makedirs(dummy_audio_dir, exist_ok=True)
            # 빈 오디오 파일 생성 (1초 무음)
            import numpy as np
            import soundfile as sf
            silence = np.zeros(16000)  # 1초 무음 (16kHz)
            dummy_path = os.path.join(dummy_audio_dir, "regional_output_1.wav")
            sf.write(dummy_path, silence, 16000)
            audio_url = "/" + dummy_path.replace("\\", "/")
            log(f"🎵 청크 {chunk_index} 더미 오디오 파일 생성 완료")
        
        # 텍스트 청크 파일 저장
        chunk_text_file = os.path.join(OUTPUT_DIR, f"{book_relative_dir}/chunk_{chunk_index}/chunk_{chunk_index}.txt")
        with open(chunk_text_file, 'w', encoding='utf-8') as f:
            f.write(chunk_text)
        
        elapsed_time = time.time() - start_time
        log(f"✅ 청크 {chunk_index} 음악 생성 및 텍스트 저장 완료 ({elapsed_time:.2f}초)")
        
        return {
            "index": chunk_index,
            "text": chunk_text[:500],
            "fullText": chunk_text,
            "emotion": chunk_context.get("emotions", "unknown"),
            "audioUrl": audio_url,
            "textUrl": f"/{OUTPUT_DIR}/{book_relative_dir}/chunk_{chunk_index}/chunk_{chunk_index}.txt",
            "duration": GEN_DURATION,
            "processing_time": elapsed_time,
            "success": True
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        log(f"❌ 청크 {chunk_index} 음악 생성 실패 ({elapsed_time:.2f}초): {e}")
        return {
            "index": chunk_index,
            "error": str(e),
            "processing_time": elapsed_time,
            "success": False
        }


async def process_all_chunks_async(
    all_chunks: List[Dict[str, Any]],
    book_relative_dir: str,
    global_prompt: str,
) -> List[Dict[str, Any]]:
    """모든 청크를 비동기로 처리합니다. 동시성은 세마포어로 제한합니다."""
    total_chunks = len(all_chunks)
    log(f"🚀 {total_chunks}개 청크를 비동기로 병렬 처리 시작...")
    
    start_time = time.time()
    
    # 동시성 제한을 위한 세마포어
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_MUSIC_GENERATION)
    
    async def limited_process_chunk(chunk_data: Dict[str, Any], chunk_index: int):
        """동시성 제한이 적용된 청크 처리"""
        async with semaphore:
            return await process_single_chunk(chunk_data, chunk_index, book_relative_dir, global_prompt)
    
    # 모든 청크를 동시에 처리 (동시성 제한 적용)
    tasks = [
        limited_process_chunk(chunk, idx + 1)
        for idx, chunk in enumerate(all_chunks)
    ]
    
    # 비동기 병렬 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 정리
    successful_chunks = []
    failed_count = 0
    total_processing_time = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed_count += 1
            log(f"❌ 청크 처리 중 예외 발생: {result}")
        elif result.get("success", False):
            successful_chunks.append(result)
            total_processing_time += result.get("processing_time", 0)
        else:
            failed_count += 1
    
    elapsed_time = time.time() - start_time
    log(f"✅ 청크 처리 완료: 성공 {len(successful_chunks)}개, 실패 {failed_count}개 (총 {elapsed_time:.2f}초)")
    return successful_chunks
