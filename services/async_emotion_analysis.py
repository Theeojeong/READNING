"""
비동기 감정선 전환점 탐지 서비스
물리적 청크 분리 후 동시다발적으로 감정 분석을 수행하는 모듈
"""

import asyncio
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from services import analyze_emotions_with_gpt
from services.split_text import split_text_with_sliding_window
from utils.logger import log

# 성능 최적화를 위한 상수
MAX_CONCURRENT_EMOTION_ANALYSIS = 8  # 동시 감정 분석 청크 수 제한
EMOTION_ANALYSIS_TIMEOUT = 45.0      # 감정 분석 타임아웃 (초)


async def analyze_chunk_emotion_async(chunk_text: str, chunk_index: int) -> Dict[str, Any]:
    """단일 청크의 감정선 전환점을 비동기로 분석"""
    start_time = time.time()
    try:
        log(f"🎭 청크 {chunk_index} 감정 분석 시작 (길이: {len(chunk_text)}자)")
        
        # 기존 analyze_emotions_with_gpt를 비동기로 실행
        log(f"📝 청크 {chunk_index} LLM 분석 요청 시작")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            analysis = await loop.run_in_executor(
                executor, 
                analyze_emotions_with_gpt, 
                chunk_text
            )
        log(f"📝 청크 {chunk_index} LLM 분석 요청 완료")
        
        elapsed_time = time.time() - start_time
        log(f"✅ 청크 {chunk_index} 감정 분석 완료 ({elapsed_time:.2f}초)")
        
        return {
            "chunk_index": chunk_index,
            "text": chunk_text,
            "analysis": analysis,
            "processing_time": elapsed_time,
            "success": True
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        log(f"❌ 청크 {chunk_index} 감정 분석 실패 ({elapsed_time:.2f}초): {e}")
        return {
            "chunk_index": chunk_index,
            "error": str(e),
            "processing_time": elapsed_time,
            "success": False
        }


async def safe_analyze_chunk_emotion(chunk_text: str, chunk_index: int, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """안전한 감정 분석 (타임아웃 및 동시성 제한)"""
    async with semaphore:
        try:
            # 타임아웃 설정
            analysis = await asyncio.wait_for(
                analyze_chunk_emotion_async(chunk_text, chunk_index),
                timeout=EMOTION_ANALYSIS_TIMEOUT
            )
            return analysis
        except asyncio.TimeoutError:
            log(f"⏰ 청크 {chunk_index} 감정 분석 타임아웃 ({EMOTION_ANALYSIS_TIMEOUT}초)")
            return {
                "chunk_index": chunk_index,
                "error": "timeout",
                "processing_time": EMOTION_ANALYSIS_TIMEOUT,
                "success": False
            }
        except Exception as e:
            log(f"❌ 청크 {chunk_index} 감정 분석 예외: {e}")
            return {
                "chunk_index": chunk_index,
                "error": str(e),
                "processing_time": 0,
                "success": False
            }


async def analyze_all_chunks_emotion_async(physical_chunks: List[str]) -> List[Dict[str, Any]]:
    """모든 물리적 청크를 동시다발적으로 감정 분석"""
    total_chunks = len(physical_chunks)
    log(f"🎭 {total_chunks}개 청크를 비동기로 감정 분석 시작...")
    
    start_time = time.time()
    
    # 동시성 제한을 위한 세마포어
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EMOTION_ANALYSIS)
    
    # 모든 청크를 동시에 처리
    tasks = [
        safe_analyze_chunk_emotion(chunk, idx, semaphore)
        for idx, chunk in enumerate(physical_chunks)
    ]
    
    # 비동기 병렬 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 정리
    successful_analyses = []
    failed_count = 0
    total_processing_time = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed_count += 1
            log(f"❌ 청크 감정 분석 중 예외 발생: {result}")
        elif result.get("success", False):
            successful_analyses.append(result)
            total_processing_time += result.get("processing_time", 0)
        else:
            failed_count += 1
    
    elapsed_time = time.time() - start_time
    log(f"✅ 감정 분석 완료: 성공 {len(successful_analyses)}개, 실패 {failed_count}개 (총 {elapsed_time:.2f}초)")
    
    return successful_analyses


async def process_book_with_async_emotion_detection(
    text: str
) -> List[Dict[str, Any]]:
    """책 전체를 비동기로 처리하는 통합 워크플로우"""
    
    log("📖 비동기 감정 분석 워크플로우 시작")
    start_time = time.time()
    
    # 1단계: 물리적 청크 분리 (슬라이딩 윈도우, 성능 최적화)
    physical_chunks = split_text_with_sliding_window(text, max_size=1500, overlap=150)
    log(f"📖 물리적 청크 분리 완료: {len(physical_chunks)}개")
    
    # 2단계: 모든 청크를 동시다발적으로 감정 분석
    emotion_analyses = await analyze_all_chunks_emotion_async(physical_chunks)
    
    # 3단계: 감정 분석 결과를 기반으로 최종 청크 생성
    final_chunks = []
    for analysis in emotion_analyses:
        if analysis["success"]:
            # 각 청크에서 감정 전환점 추출
            emotional_phases = analysis["analysis"].get("emotional_phases", [])
            
            if emotional_phases:
                # 감정 전환점이 있으면 세분화
                chunk_text = analysis["text"]
                last_pos = 0
                
                for phase in emotional_phases:
                    phase_pos = phase.get("position_in_full_text", 0)
                    if phase_pos > last_pos:
                        sub_chunk = chunk_text[last_pos:phase_pos].strip()
                        if sub_chunk and len(sub_chunk) > 10:
                            final_chunks.append({
                                "text": sub_chunk,
                                "context": {
                                    "emotions": phase.get("emotions_before", "unknown"),
                                    "transition": phase.get("emotions_after", "unknown"),
                                    "significance": phase.get("significance", 1),
                                    "explanation": phase.get("explanation", "")
                                }
                            })
                        last_pos = phase_pos
                
                # 마지막 부분 처리
                if last_pos < len(chunk_text):
                    final_chunk = chunk_text[last_pos:].strip()
                    if final_chunk and len(final_chunk) > 10:
                        final_chunks.append({
                            "text": final_chunk,
                            "context": {
                                "emotions": emotional_phases[-1].get("emotions_after", "unknown")
                            }
                        })
            else:
                # 감정 전환점이 없으면 전체 청크 사용
                final_chunks.append({
                    "text": analysis["text"],
                    "context": {"emotions": "neutral"}
                })
    
    elapsed_time = time.time() - start_time
    log(f"🎭 비동기 감정 분석 워크플로우 완료: {len(final_chunks)}개 청크 생성 (총 {elapsed_time:.2f}초)")
    return final_chunks
