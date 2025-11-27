"""
Chunk processing utilities following Single Responsibility Principle.

Each function has ONE clear purpose and minimal dependencies.
"""

from typing import List, Dict, Any, Optional, Tuple
from services.types import TextChunk, EmotionalPhase, Result
from services.error_handler import ErrorCode, validate_result
from config import MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, SIGNIFICANCE_THRESHOLD
from utils.logger import log


# ============================================================================
# Position Calculation
# ============================================================================

def calculate_phase_position(
    segment: str,
    phase: EmotionalPhase
) -> Optional[int]:
    """
    Calculate the exact position of an emotional phase in the segment.

    Uses fuzzy matching if exact match fails.

    Args:
        segment: The full text segment
        phase: The emotional phase to locate

    Returns:
        Character position or None if not found
    """
    start_text = phase.start_text.strip()

    if not start_text:
        log("⚠️ Empty start_text, cannot calculate position")
        return None

    # Try exact match first
    position = segment.find(start_text)

    if position != -1:
        return position

    # Try fuzzy match with first 30 characters
    short_start = start_text[:30]
    position = segment.find(short_start)

    if position != -1:
        log(f"✅ Fuzzy match found at position {position}")
        return position

    log(f"⚠️ Position not found for: '{start_text[:50]}...'")
    return None


def sort_phases_by_position(
    phases: List[EmotionalPhase]
) -> List[EmotionalPhase]:
    """
    Sort emotional phases by their position in text.

    Phases without position are placed at the end.

    Args:
        phases: List of emotional phases

    Returns:
        Sorted list of phases
    """
    return sorted(
        phases,
        key=lambda p: (
            p.position_in_full_text if p.position_in_full_text is not None
            else float('inf')
        )
    )


def filter_significant_phases(
    phases: List[EmotionalPhase],
    threshold: int = SIGNIFICANCE_THRESHOLD
) -> List[EmotionalPhase]:
    """
    Filter phases by significance threshold.

    Only phases with significance >= threshold are kept.

    Args:
        phases: List of emotional phases
        threshold: Minimum significance level (1-5)

    Returns:
        Filtered list of significant phases
    """
    filtered = [p for p in phases if p.significance >= threshold]

    if len(filtered) < len(phases):
        log(
            f"🎯 Filtered {len(phases)} phases → {len(filtered)} significant "
            f"(threshold: {threshold})"
        )

    return filtered


# ============================================================================
# Chunk Validation
# ============================================================================

def validate_chunk_size(text: str) -> Optional[Result]:
    """
    Validate that chunk size is within acceptable bounds.

    Args:
        text: The chunk text to validate

    Returns:
        Error Result if invalid, None if valid
    """
    text_length = len(text)

    if text_length < MIN_CHUNK_SIZE:
        return Result.fail(
            error=f"Chunk too small: {text_length} < {MIN_CHUNK_SIZE}",
            error_code=ErrorCode.CHUNK_TOO_SMALL
        )

    if text_length > MAX_CHUNK_SIZE:
        return Result.fail(
            error=f"Chunk too large: {text_length} > {MAX_CHUNK_SIZE}",
            error_code=ErrorCode.CHUNK_TOO_LARGE
        )

    return None


def is_valid_chunk(chunk_text: str) -> bool:
    """
    Check if chunk is valid for processing.

    Args:
        chunk_text: Text to validate

    Returns:
        True if valid, False otherwise
    """
    if not chunk_text or not chunk_text.strip():
        return False

    return MIN_CHUNK_SIZE <= len(chunk_text) <= MAX_CHUNK_SIZE


# ============================================================================
# Chunk Splitting Logic
# ============================================================================

def split_text_by_phases(
    text: str,
    phases: List[EmotionalPhase]
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Split text into chunks based on emotional phases.

    This is the core algorithm for emotion-based text segmentation.

    Args:
        text: Full text to split
        phases: Sorted emotional phases with positions

    Returns:
        List of (chunk_text, context) tuples

    Algorithm:
        1. Iterate through phases in position order
        2. Extract text from last_pos to current phase position
        3. Validate chunk size
        4. Attach emotional context
        5. Handle remaining text at the end
    """
    if not phases:
        return []

    chunks: List[Tuple[str, Dict[str, Any]]] = []
    last_pos = 0

    # Filter out phases without valid position
    valid_phases = [p for p in phases if p.position_in_full_text is not None]

    if not valid_phases:
        log("⚠️ No valid phases with positions")
        return []

    for phase in valid_phases:
        phase_pos = phase.position_in_full_text

        # Validate position ordering
        if phase_pos <= last_pos:
            log(f"⚠️ Invalid position order: {phase_pos} <= {last_pos}, skipping")
            continue

        # Extract chunk
        chunk_text = text[last_pos:phase_pos].strip()

        # Validate size
        if not is_valid_chunk(chunk_text):
            log(f"⚠️ Invalid chunk size ({len(chunk_text)} chars), skipping")
            continue

        # Create context
        context = {
            "emotions": phase.emotions_before,
            "transition": phase.emotions_after,
            "significance": phase.significance,
            "explanation": phase.explanation,
        }

        chunks.append((chunk_text, context))
        last_pos = phase_pos

    # Handle remaining text
    if last_pos < len(text):
        final_text = text[last_pos:].strip()

        if is_valid_chunk(final_text):
            context = {
                "emotions": valid_phases[-1].emotions_after if valid_phases else "neutral"
            }
            chunks.append((final_text, context))
        elif chunks:
            # Merge with previous chunk if too small
            log(f"✂️ Merging small trailing chunk ({len(final_text)} chars)")
            prev_text, prev_context = chunks[-1]
            chunks[-1] = (prev_text + " " + final_text, prev_context)

    return chunks


def create_text_chunks(
    chunks_data: List[Tuple[str, Dict[str, Any]]]
) -> List[TextChunk]:
    """
    Convert raw chunk data into TextChunk value objects.

    Args:
        chunks_data: List of (text, context) tuples

    Returns:
        List of validated TextChunk objects
    """
    text_chunks = []

    for text, context in chunks_data:
        try:
            chunk = TextChunk(text=text, context=context)
            text_chunks.append(chunk)
        except Exception as e:
            log(f"❌ Failed to create TextChunk: {e}")
            continue

    return text_chunks


# ============================================================================
# Chunk Merging
# ============================================================================

def merge_small_chunks(
    chunks: List[Tuple[str, Dict[str, Any]]],
    min_size: int = MIN_CHUNK_SIZE
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Merge consecutive small chunks to meet minimum size requirement.

    Args:
        chunks: List of (text, context) tuples
        min_size: Minimum chunk size

    Returns:
        List with small chunks merged
    """
    if not chunks:
        return []

    merged = []
    i = 0

    while i < len(chunks):
        current_text, current_context = chunks[i]

        # If current chunk is too small and not the last one
        if len(current_text) < min_size and i < len(chunks) - 1:
            next_text, next_context = chunks[i + 1]
            merged_text = current_text + " " + next_text
            # Keep the first chunk's context
            merged.append((merged_text, current_context))
            log(f"✂️ Merged chunks {i} and {i+1} ({len(merged_text)} chars)")
            i += 2  # Skip next chunk
        else:
            merged.append((current_text, current_context))
            i += 1

    return merged


# ============================================================================
# Statistics
# ============================================================================

def calculate_chunk_statistics(
    chunks: List[TextChunk]
) -> Dict[str, Any]:
    """
    Calculate statistics about processed chunks.

    Args:
        chunks: List of text chunks

    Returns:
        Dictionary with statistics
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "average_size": 0,
            "min_size": 0,
            "max_size": 0,
            "total_characters": 0,
        }

    chunk_sizes = [len(chunk.text) for chunk in chunks]

    return {
        "total_chunks": len(chunks),
        "average_size": sum(chunk_sizes) // len(chunk_sizes),
        "min_size": min(chunk_sizes),
        "max_size": max(chunk_sizes),
        "total_characters": sum(chunk_sizes),
    }
