"""공통 유틸리티 함수들"""
import os
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from utils.file_utils import save_text_to_file, ensure_dir, secure_filename
from services import chunk_text_by_emotion, prompt_service
from config import OUTPUT_DIR


def process_text_chunks(text: str, tmp_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """텍스트를 감정 기반으로 청크 분할"""
    save_text_to_file(tmp_path, text)
    return chunk_text_by_emotion.chunk_text_by_emotion(tmp_path)


def generate_music_prompts(text: str, chunks: List[Tuple[str, Dict[str, Any]]], 
                          preference: List[str] = None) -> Tuple[str, List[str]]:
    """글로벌 및 지역 음악 프롬프트 생성"""
    global_prompt = prompt_service.generate_global(text)
    music_prompts = []
    
    for chunk in chunks:
        chunk_text = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
        regional = prompt_service.generate_regional(chunk_text)
        
        if preference:
            pref_line = f"User preference: {', '.join(preference)}"
            regional = f"{regional}\n{pref_line}"
            
        music_prompts.append(
            prompt_service.compose_musicgen_prompt(global_prompt, regional)
        )
    
    return global_prompt, music_prompts


def parse_preference(preference_str: str) -> List[str]:
    """선호도 JSON 문자열 파싱"""
    try:
        pref_list = json.loads(preference_str)
        if not isinstance(pref_list, list):
            raise ValueError("Not a list")
        return pref_list
    except Exception:
        return []


def setup_book_directory(user_id: str, book_title: str, page: int = None) -> Tuple[str, str]:
    """책 디렉토리 설정 및 경로 반환"""
    safe_title = secure_filename(book_title)
    book_dir = os.path.join(user_id, safe_title)
    abs_book_dir = os.path.join(OUTPUT_DIR, book_dir)
    ensure_dir(abs_book_dir)
    
    if page is not None:
        tmp_path = os.path.join(abs_book_dir, f"ch{page}_tmp.txt")
    else:
        tmp_path = os.path.join(abs_book_dir, "tmp.txt")
    
    return book_dir, tmp_path