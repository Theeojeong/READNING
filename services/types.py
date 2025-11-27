"""
Type definitions for the music generation workflow.

This module provides type-safe data structures following Clean Code principles.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# Enums - Explicit State Definition
# ============================================================================

class EmotionType(str, Enum):
    """Enumeration of possible emotion types."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    CONTENTMENT = "contentment"
    ANXIETY = "anxiety"
    HOPE = "hope"
    DETERMINATION = "determination"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of a processing task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Value Objects - Immutable Domain Models
# ============================================================================

class EmotionalPhase(BaseModel):
    """
    Value object representing an emotional transition point in text.

    Immutable by design - represents a single emotional shift.
    """
    start_text: str = Field(
        ...,
        description="Text snippet at transition point",
        min_length=1,
        max_length=100
    )
    emotions_before: str = Field(
        ...,
        description="Emotions before transition (comma-separated)"
    )
    emotions_after: str = Field(
        ...,
        description="Emotions after transition (comma-separated)"
    )
    significance: int = Field(
        ...,
        description="Importance of transition (1-5)",
        ge=1,
        le=5
    )
    explanation: str = Field(
        ...,
        description="Why this transition matters musically",
        max_length=200
    )
    position_in_full_text: Optional[int] = Field(
        default=None,
        description="Character index in original text",
        ge=0
    )

    class Config:
        frozen = True  # Immutability

    @validator('emotions_before', 'emotions_after')
    def validate_emotions(cls, v):
        """Ensure emotions are properly formatted."""
        if not v or not v.strip():
            raise ValueError("Emotions cannot be empty")
        return v.strip()


class TextChunk(BaseModel):
    """
    Value object representing a chunk of text with emotional context.

    This is the atomic unit for music generation.
    """
    text: str = Field(..., description="The actual text content", min_length=1)
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Emotional and musical context"
    )

    class Config:
        frozen = True

    @validator('text')
    def validate_text(cls, v):
        """Ensure text is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class ChunkMetadata(BaseModel):
    """
    Metadata for a processed chunk after music generation.

    Contains all information needed for playback and storage.
    """
    chunk_index: int = Field(..., ge=0)
    text_preview: str = Field(..., max_length=300)
    music_file_path: str
    emotions: str
    duration: int = Field(..., gt=0)
    page: Optional[int] = Field(default=None, ge=1)

    class Config:
        frozen = True


# ============================================================================
# DTOs - Data Transfer Objects
# ============================================================================

class EmotionAnalysisRequest(BaseModel):
    """Request for emotion analysis."""
    segment: str = Field(..., min_length=10)

    class Config:
        frozen = True


class EmotionAnalysisResult(BaseModel):
    """Result of emotion analysis."""
    emotional_phases: List[EmotionalPhase] = Field(
        default_factory=list,
        description="List of detected emotional transition points"
    )

    @validator('emotional_phases')
    def validate_phases(cls, v):
        """Ensure phases are sorted by position."""
        if not v:
            return v

        # Filter out phases without position
        valid_phases = [p for p in v if p.position_in_full_text is not None]

        # Sort by position
        valid_phases.sort(key=lambda x: x.position_in_full_text)

        return valid_phases


class MusicGenerationRequest(BaseModel):
    """Request for music generation."""
    chunks: List[TextChunk]
    book_dir: str
    global_prompt: str

    class Config:
        frozen = True


class WorkflowResult(BaseModel):
    """Final result of the workflow execution."""
    message: str
    book_id: str
    text_length: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=0)
    total_duration: int = Field(..., ge=0)
    successful_pages: int = Field(..., ge=0)
    pages: List[Dict[str, Any]]
    processing_method: Literal["langgraph_workflow"] = "langgraph_workflow"
    processing_times: Dict[str, float] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# State Objects - Workflow State Management
# ============================================================================

class WorkflowState(TypedDict, total=False):
    """
    State object for LangGraph workflow.

    Uses TypedDict for better IDE support and type checking.
    """
    # Input data
    text: str
    user_name: str
    book_title: str
    book_id: str
    book_dir: str

    # Intermediate processing results
    physical_chunks: List[str]
    emotion_analyses: List[Dict[str, Any]]
    final_chunks: List[Dict[str, Any]]
    chunk_metadata: List[Dict[str, Any]]

    # Final results
    page_chunk_mapping: Dict[int, Dict[str, Any]]
    page_results: List[Dict[str, Any]]
    total_duration: int
    successful_pages: int

    # Metadata
    processing_times: Dict[str, float]
    errors: List[str]


# ============================================================================
# Result Type - Functional Error Handling
# ============================================================================

class Result(BaseModel):
    """
    Result type for functional error handling.

    Inspired by Rust's Result<T, E> pattern.
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def ok(cls, data: Any = None) -> "Result":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str, error_code: Optional[str] = None) -> "Result":
        """Create a failed result."""
        return cls(success=False, error=error, error_code=error_code)

    def unwrap(self) -> Any:
        """
        Unwrap the result data.

        Raises ValueError if the result is a failure.
        """
        if not self.success:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.data

    def unwrap_or(self, default: Any) -> Any:
        """Unwrap the result data or return default if failed."""
        return self.data if self.success else default

    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self.success

    def is_err(self) -> bool:
        """Check if result is failed."""
        return not self.success
