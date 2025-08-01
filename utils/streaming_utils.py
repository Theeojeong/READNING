"""대용량 파일을 위한 스트리밍 처리 유틸리티"""
import os
from typing import Generator, Iterator
from utils.logger import log


def read_file_in_chunks(file_path: str, chunk_size: int = 8192) -> Generator[str, None, None]:
    """파일을 청크 단위로 스트리밍 읽기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except Exception as e:
        log(f"스트리밍 파일 읽기 오류: {e}")
        return


def process_large_text_streaming(file_path: str, max_memory_mb: int = 100) -> Iterator[str]:
    """메모리 사용량을 제한하며 대용량 텍스트 처리"""
    file_size = os.path.getsize(file_path)
    max_bytes = max_memory_mb * 1024 * 1024
    
    if file_size <= max_bytes:
        # 작은 파일은 일반 처리
        with open(file_path, 'r', encoding='utf-8') as f:
            yield f.read()
    else:
        # 큰 파일은 청크 단위 처리
        log(f"대용량 파일 감지 ({file_size:,} bytes): 스트리밍 모드")
        buffer = ""
        sentence_endings = ['.', '!', '?', '。', '！', '？']
        
        for chunk in read_file_in_chunks(file_path, 4096):
            buffer += chunk
            
            # 문장 경계에서 yield
            for ending in sentence_endings:
                if ending in buffer:
                    sentences = buffer.split(ending)
                    for i in range(len(sentences) - 1):
                        yield sentences[i] + ending
                    buffer = sentences[-1]
                    break
        
        # 남은 버퍼 처리
        if buffer.strip():
            yield buffer


def get_file_info(file_path: str) -> dict:
    """파일 정보 반환 (크기, 인코딩 추정 등)"""
    import chardet
    
    file_size = os.path.getsize(file_path)
    
    # 인코딩 추정 (처음 1KB만 사용)
    with open(file_path, 'rb') as f:
        raw_data = f.read(min(1024, file_size))
        encoding_info = chardet.detect(raw_data)
    
    return {
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "estimated_encoding": encoding_info.get("encoding", "unknown"),
        "encoding_confidence": encoding_info.get("confidence", 0.0),
        "is_large_file": file_size > 10 * 1024 * 1024  # 10MB 이상
    }