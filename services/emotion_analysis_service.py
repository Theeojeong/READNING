"""
Emotion Analysis Service - Clean Architecture Implementation.

This service follows SOLID principles and separates concerns properly.
"""

import asyncio
from typing import List, Dict, Any
from services.types import (
    EmotionAnalysisRequest,
    EmotionAnalysisResult,
    EmotionalPhase,
    Result
)
from services.error_handler import (
    safe_execute_async,
    retry_on_failure,
    ErrorCode
)
from services.chunk_processor import (
    calculate_phase_position,
    sort_phases_by_position,
    filter_significant_phases
)
from services.get_emotion_analysis_prompt import get_emotion_analysis_prompt
from services.model_manager import ollama_manager
from config import SIGNIFICANCE_THRESHOLD, MAX_CONCURRENT_EMOTION_ANALYSIS
from utils.logger import log


class EmotionAnalysisService:
    """
    Service for analyzing emotional content in text.

    Responsibilities:
    - Analyze text segments for emotional transitions
    - Calculate positions of emotional phases
    - Filter phases by significance
    - Coordinate batch processing

    Dependencies are injected for testability.
    """

    def __init__(
        self,
        model_manager=None,
        significance_threshold: int = SIGNIFICANCE_THRESHOLD
    ):
        """
        Initialize the emotion analysis service.

        Args:
            model_manager: LLM model manager (injectable for testing)
            significance_threshold: Minimum significance for phase filtering
        """
        self.model_manager = model_manager or ollama_manager
        self.significance_threshold = significance_threshold

    async def analyze_segment(
        self,
        segment: str,
        retry_attempts: int = 3
    ) -> Result:
        """
        Analyze a single text segment for emotional transitions.

        This is the core analysis method that coordinates:
        1. LLM emotion analysis
        2. Position calculation
        3. Significance filtering

        Args:
            segment: Text segment to analyze
            retry_attempts: Number of retry attempts on failure

        Returns:
            Result containing EmotionAnalysisResult or error
        """
        if not segment or len(segment) < 10:
            return Result.fail(
                error="Segment too short for analysis",
                error_code=ErrorCode.TEXT_TOO_SHORT
            )

        log(f"🔍 Analyzing segment ({len(segment)} chars)")

        # Execute with retry logic
        result = await self._analyze_with_retry(segment, retry_attempts)

        if result.is_err():
            return result

        raw_phases = result.unwrap()

        # Post-process phases
        processed_result = self._post_process_phases(segment, raw_phases)

        return Result.ok(processed_result)

    async def _analyze_with_retry(
        self,
        segment: str,
        max_attempts: int
    ) -> Result:
        """
        Execute LLM analysis with retry logic.

        Args:
            segment: Text to analyze
            max_attempts: Maximum retry attempts

        Returns:
            Result containing raw phases data
        """
        prompt = get_emotion_analysis_prompt(segment)

        for attempt in range(1, max_attempts + 1):
            log(f"🔄 Analysis attempt {attempt}/{max_attempts}")

            result = await safe_execute_async(
                self._call_llm,
                prompt,
                error_message=f"LLM analysis failed (attempt {attempt})",
                error_code=ErrorCode.EMOTION_ANALYSIS_FAILED
            )

            if result.is_ok():
                return result

            if attempt < max_attempts:
                await asyncio.sleep(1.0)  # Delay before retry

        return Result.fail(
            error=f"Analysis failed after {max_attempts} attempts",
            error_code=ErrorCode.EMOTION_ANALYSIS_FAILED
        )

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM model for emotion analysis.

        Args:
            prompt: Analysis prompt

        Returns:
            Raw LLM response data
        """
        messages = [{"role": "user", "content": prompt}]

        # Using structured output from Pydantic model
        from services.analyze_emotions_with_gpt import EmotionAnalysisResult as LegacyResult

        result = self.model_manager.chat_with_structured_output(
            messages,
            LegacyResult
        )

        return result

    def _post_process_phases(
        self,
        segment: str,
        raw_data: Dict[str, Any]
    ) -> EmotionAnalysisResult:
        """
        Post-process raw LLM response.

        Steps:
        1. Extract phases from raw data
        2. Calculate positions
        3. Filter by significance
        4. Sort by position
        5. Validate and create result object

        Args:
            segment: Original text segment
            raw_data: Raw LLM response

        Returns:
            Processed EmotionAnalysisResult
        """
        phases = raw_data.get("emotional_phases", [])

        if not phases:
            log("ℹ️ No emotional phases detected")
            return EmotionAnalysisResult(emotional_phases=[])

        # Calculate positions for each phase
        enriched_phases = self._calculate_positions(segment, phases)

        # Filter by significance
        significant_phases = filter_significant_phases(
            enriched_phases,
            self.significance_threshold
        )

        # Sort by position
        sorted_phases = sort_phases_by_position(significant_phases)

        log(
            f"✅ Analysis complete: {len(phases)} phases → "
            f"{len(significant_phases)} significant → "
            f"{len(sorted_phases)} final"
        )

        return EmotionAnalysisResult(emotional_phases=sorted_phases)

    def _calculate_positions(
        self,
        segment: str,
        raw_phases: List[Dict[str, Any]]
    ) -> List[EmotionalPhase]:
        """
        Calculate positions for all phases.

        Args:
            segment: Original text
            raw_phases: Raw phase data from LLM

        Returns:
            List of EmotionalPhase objects with positions
        """
        enriched_phases = []

        for raw_phase in raw_phases:
            try:
                # Convert to Pydantic model
                phase = EmotionalPhase(**raw_phase)

                # Calculate position
                position = calculate_phase_position(segment, phase)

                # Create new phase with position
                enriched_phase = EmotionalPhase(
                    **phase.dict(exclude={'position_in_full_text'}),
                    position_in_full_text=position
                )

                enriched_phases.append(enriched_phase)

            except Exception as e:
                log(f"⚠️ Failed to process phase: {e}")
                continue

        return enriched_phases

    async def analyze_batch(
        self,
        segments: List[str],
        max_concurrent: int = MAX_CONCURRENT_EMOTION_ANALYSIS
    ) -> List[Result]:
        """
        Analyze multiple segments concurrently with rate limiting.

        Args:
            segments: List of text segments to analyze
            max_concurrent: Maximum concurrent analyses

        Returns:
            List of Results (one per segment)
        """
        log(f"🎭 Batch analysis: {len(segments)} segments "
            f"(concurrency: {max_concurrent})")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_limit(segment: str, index: int) -> Result:
            async with semaphore:
                log(f"📊 Analyzing segment {index + 1}/{len(segments)}")
                return await self.analyze_segment(segment)

        tasks = [
            analyze_with_limit(seg, i)
            for i, seg in enumerate(segments)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to Results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    Result.fail(
                        error=f"Segment {i} analysis failed: {str(result)}",
                        error_code=ErrorCode.EMOTION_ANALYSIS_FAILED
                    )
                )
            else:
                processed_results.append(result)

        successful = sum(1 for r in processed_results if r.is_ok())
        log(f"✅ Batch complete: {successful}/{len(segments)} successful")

        return processed_results


# ============================================================================
# Factory Function - Dependency Injection
# ============================================================================

def create_emotion_analysis_service(
    model_manager=None,
    significance_threshold: int = SIGNIFICANCE_THRESHOLD
) -> EmotionAnalysisService:
    """
    Factory function for creating EmotionAnalysisService.

    This allows for easy dependency injection and testing.

    Args:
        model_manager: Custom model manager (for testing)
        significance_threshold: Custom threshold (for tuning)

    Returns:
        Configured EmotionAnalysisService instance
    """
    return EmotionAnalysisService(
        model_manager=model_manager,
        significance_threshold=significance_threshold
    )


# Singleton instance for backward compatibility
_default_service: EmotionAnalysisService = None


def get_emotion_analysis_service() -> EmotionAnalysisService:
    """
    Get or create the default emotion analysis service.

    Returns:
        Default service instance
    """
    global _default_service
    if _default_service is None:
        _default_service = create_emotion_analysis_service()
    return _default_service
