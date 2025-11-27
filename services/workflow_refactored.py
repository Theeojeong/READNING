"""
Refactored LangGraph Workflow - Clean Architecture Implementation.

Key Improvements:
1. Single Responsibility - Each node does ONE thing
2. Dependency Injection - Services are injected, not imported
3. Type Safety - Strong typing throughout
4. Error Handling - Functional error handling with Result type
5. Testability - All dependencies can be mocked
6. Immutability - State transitions are explicit
7. Observability - Detailed metrics and logging
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from services.types import (
    WorkflowState,
    WorkflowResult,
    TextChunk,
    Result
)
from services.error_handler import safe_execute_async, ErrorCode
from services.emotion_analysis_service import EmotionAnalysisService
from services.chunk_processor import (
    split_text_by_phases,
    create_text_chunks,
    merge_small_chunks,
    calculate_chunk_statistics
)
from services.split_text import split_text_with_sliding_window
from services.async_music_generation import process_all_chunks_async
from services.mysql_service import mysql_service
from services import prompt_service
from utils.logger import log
from config import (
    GEN_DURATION,
    CHUNKS_PER_PAGE,
    MAX_SEGMENT_SIZE,
    OVERLAP_SIZE
)


class MusicGenerationWorkflowRefactored:
    """
    Refactored music generation workflow using Clean Architecture.

    Principles Applied:
    - Dependency Inversion: Dependencies are injected
    - Open/Closed: Easy to extend without modification
    - Single Responsibility: Each method has ONE job
    - Interface Segregation: Clear contracts between components
    """

    def __init__(
        self,
        emotion_service: Optional[EmotionAnalysisService] = None,
        music_generator=None,
        database_service=None
    ):
        """
        Initialize workflow with dependency injection.

        Args:
            emotion_service: Service for emotion analysis
            music_generator: Service for music generation
            database_service: Service for database operations
        """
        # Dependency injection with defaults
        self.emotion_service = emotion_service or EmotionAnalysisService()
        self.music_generator = music_generator or process_all_chunks_async
        self.database_service = database_service or mysql_service

        self.graph = self._build_graph()

    # ========================================================================
    # Graph Construction
    # ========================================================================

    def _build_graph(self) -> StateGraph:
        """
        Build the workflow graph with clear node definitions.

        Returns:
            Compiled LangGraph workflow
        """
        workflow = StateGraph(WorkflowState)

        # Add nodes - each with a single responsibility
        workflow.add_node("split_text", self._split_text_node)
        workflow.add_node("analyze_emotions", self._analyze_emotions_node)
        workflow.add_node("create_chunks", self._create_chunks_node)
        workflow.add_node("generate_music", self._generate_music_node)
        workflow.add_node("create_pages", self._create_pages_node)
        workflow.add_node("save_to_db", self._save_to_db_node)

        # Define edges - workflow progression
        workflow.set_entry_point("split_text")
        workflow.add_edge("split_text", "analyze_emotions")
        workflow.add_edge("analyze_emotions", "create_chunks")
        workflow.add_edge("create_chunks", "generate_music")
        workflow.add_edge("generate_music", "create_pages")
        workflow.add_edge("create_pages", "save_to_db")
        workflow.add_edge("save_to_db", END)

        return workflow.compile()

    # ========================================================================
    # Node Implementations - Each with Single Responsibility
    # ========================================================================

    async def _split_text_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 1: Split text into physical chunks.

        Responsibility: Text segmentation only
        Input: Full text
        Output: List of physical chunks
        """
        start_time = time.time()
        log("📖 Step 1/6: Splitting text into segments")

        result = await safe_execute_async(
            self._split_text_logic,
            state["text"],
            error_message="Text splitting failed",
            error_code=ErrorCode.TEXT_SPLIT_FAILED
        )

        if result.is_err():
            return self._handle_error(state, "split_text", result.error)

        physical_chunks = result.unwrap()
        elapsed = time.time() - start_time

        log(f"✅ Text split: {len(physical_chunks)} segments ({elapsed:.2f}s)")

        return {
            **state,
            "physical_chunks": physical_chunks,
            "processing_times": {
                **state.get("processing_times", {}),
                "split_text": elapsed
            }
        }

    async def _analyze_emotions_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 2: Analyze emotions in each physical chunk.

        Responsibility: Emotion detection only
        Input: Physical chunks
        Output: Emotion analysis results
        """
        start_time = time.time()
        chunks = state.get("physical_chunks", [])

        log(f"🎭 Step 2/6: Analyzing emotions in {len(chunks)} segments")

        # Batch analysis with the service
        results = await self.emotion_service.analyze_batch(chunks)

        # Convert Results to compatible format
        emotion_analyses = []
        for i, result in enumerate(results):
            if result.is_ok():
                analysis_result = result.unwrap()
                emotion_analyses.append({
                    "chunk_index": i,
                    "text": chunks[i],
                    "analysis": analysis_result.dict(),
                    "success": True
                })
            else:
                emotion_analyses.append({
                    "chunk_index": i,
                    "text": chunks[i],
                    "error": result.error,
                    "success": False
                })

        elapsed = time.time() - start_time
        successful = sum(1 for a in emotion_analyses if a["success"])

        log(f"✅ Emotion analysis: {successful}/{len(chunks)} successful ({elapsed:.2f}s)")

        return {
            **state,
            "emotion_analyses": emotion_analyses,
            "processing_times": {
                **state.get("processing_times", {}),
                "analyze_emotions": elapsed
            }
        }

    async def _create_chunks_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 3: Create final chunks based on emotion analysis.

        Responsibility: Chunk creation and merging
        Input: Emotion analyses
        Output: Final text chunks with context
        """
        start_time = time.time()
        log("✂️ Step 3/6: Creating final chunks from emotion analysis")

        result = await safe_execute_async(
            self._create_chunks_logic,
            state.get("emotion_analyses", []),
            error_message="Chunk creation failed",
            error_code=ErrorCode.INVALID_CHUNK_DATA
        )

        if result.is_err():
            return self._handle_error(state, "create_chunks", result.error)

        final_chunks = result.unwrap()
        elapsed = time.time() - start_time

        # Calculate statistics
        stats = calculate_chunk_statistics(final_chunks)

        log(f"✅ Chunks created: {stats['total_chunks']} chunks")
        log(f"   - Avg size: {stats['average_size']} chars")
        log(f"   - Range: {stats['min_size']}-{stats['max_size']} chars")
        log(f"   - Time: {elapsed:.2f}s")

        return {
            **state,
            "final_chunks": [chunk.dict() for chunk in final_chunks],
            "processing_times": {
                **state.get("processing_times", {}),
                "create_chunks": elapsed
            }
        }

    async def _generate_music_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 4: Generate music for each chunk.

        Responsibility: Music generation only
        Input: Final chunks
        Output: Chunk metadata with music files
        """
        start_time = time.time()
        chunks = state.get("final_chunks", [])

        log(f"🎵 Step 4/6: Generating music for {len(chunks)} chunks")

        # Generate global prompt
        global_prompt = prompt_service.generate_global(state["text"])

        # Generate music for all chunks
        chunk_metadata = await self.music_generator(
            chunks,
            state["book_dir"],
            global_prompt
        )

        elapsed = time.time() - start_time

        log(f"✅ Music generated: {len(chunk_metadata)} tracks ({elapsed:.2f}s)")

        return {
            **state,
            "chunk_metadata": chunk_metadata,
            "processing_times": {
                **state.get("processing_times", {}),
                "generate_music": elapsed
            }
        }

    async def _create_pages_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 5: Create page mappings from chunks.

        Responsibility: Page organization
        Input: Chunk metadata
        Output: Page chunk mapping
        """
        start_time = time.time()
        log("📄 Step 5/6: Creating page mappings")

        result = await safe_execute_async(
            self._create_page_mapping_logic,
            state.get("chunk_metadata", []),
            error_message="Page mapping failed"
        )

        if result.is_err():
            return self._handle_error(state, "create_pages", result.error)

        page_mapping = result.unwrap()
        elapsed = time.time() - start_time

        log(f"✅ Pages organized: {len(page_mapping)} pages ({elapsed:.2f}s)")

        return {
            **state,
            "page_chunk_mapping": page_mapping,
            "processing_times": {
                **state.get("processing_times", {}),
                "create_pages": elapsed
            }
        }

    async def _save_to_db_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node 6: Save results to database.

        Responsibility: Data persistence
        Input: Page mapping and metadata
        Output: Page results
        """
        start_time = time.time()
        log("💾 Step 6/6: Saving to database")

        result = await safe_execute_async(
            self._save_to_database_logic,
            state,
            error_message="Database save failed",
            error_code=ErrorCode.DATABASE_WRITE_FAILED
        )

        if result.is_err():
            return self._handle_error(state, "save_to_db", result.error)

        page_results, total_duration, successful_pages = result.unwrap()
        elapsed = time.time() - start_time

        log(f"✅ Database save: {successful_pages} pages saved ({elapsed:.2f}s)")

        return {
            **state,
            "page_results": page_results,
            "total_duration": total_duration,
            "successful_pages": successful_pages,
            "processing_times": {
                **state.get("processing_times", {}),
                "save_to_db": elapsed
            }
        }

    # ========================================================================
    # Business Logic - Separated from Node Orchestration
    # ========================================================================

    async def _split_text_logic(self, text: str) -> List[str]:
        """Business logic for text splitting."""
        return split_text_with_sliding_window(
            text,
            max_size=MAX_SEGMENT_SIZE,
            overlap=OVERLAP_SIZE
        )

    async def _create_chunks_logic(
        self,
        emotion_analyses: List[Dict[str, Any]]
    ) -> List[TextChunk]:
        """Business logic for chunk creation."""
        all_chunks = []

        for analysis in emotion_analyses:
            if not analysis.get("success"):
                continue

            text = analysis["text"]
            phases_data = analysis["analysis"].get("emotional_phases", [])

            if not phases_data:
                # No phases - use whole chunk
                from services.chunk_processor import is_valid_chunk
                if is_valid_chunk(text):
                    chunk = TextChunk(text=text, context={"emotions": "neutral"})
                    all_chunks.append(chunk)
                continue

            # Convert to EmotionalPhase objects
            from services.types import EmotionalPhase
            phases = [EmotionalPhase(**p) for p in phases_data]

            # Split by phases
            raw_chunks = split_text_by_phases(text, phases)

            # Merge small chunks
            merged_chunks = merge_small_chunks(raw_chunks)

            # Create TextChunk objects
            text_chunks = create_text_chunks(merged_chunks)

            all_chunks.extend(text_chunks)

        return all_chunks

    async def _create_page_mapping_logic(
        self,
        chunk_metadata: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """Business logic for page mapping creation."""
        page_mapping = {}

        for i, chunk in enumerate(chunk_metadata):
            page_num = (i // CHUNKS_PER_PAGE) + 1

            if page_num not in page_mapping:
                page_mapping[page_num] = {
                    "start_index": i + 1,
                    "end_index": i + 1,
                    "chunk_count": 0
                }

            page_mapping[page_num]["end_index"] = i + 1
            page_mapping[page_num]["chunk_count"] += 1
            chunk["page"] = page_num

        return page_mapping

    async def _save_to_database_logic(
        self,
        state: WorkflowState
    ) -> tuple[List[Dict[str, Any]], int, int]:
        """Business logic for database persistence."""
        page_mapping = state["page_chunk_mapping"]
        chunk_metadata = state["chunk_metadata"]
        book_id = state["book_id"]
        book_title = state["book_title"]

        page_results = []

        for page_num, mapping in page_mapping.items():
            start_idx = mapping["start_index"] - 1
            end_idx = mapping["end_index"]
            page_chunks = chunk_metadata[start_idx:end_idx]

            if not page_chunks:
                page_results.append({
                    "page": page_num,
                    "chunks": 0,
                    "duration": 0,
                    "error": "No chunks"
                })
                continue

            page_duration = len(page_chunks) * GEN_DURATION

            try:
                self.database_service.save_chapter_chunks(
                    book_id=book_id,
                    page=page_num,
                    chunks=page_chunks,
                    total_duration=page_duration,
                    book_title=book_title
                )

                page_results.append({
                    "page": page_num,
                    "chunks": len(page_chunks),
                    "duration": page_duration,
                    "cached": False
                })
            except Exception as e:
                log(f"❌ Failed to save page {page_num}: {e}")
                page_results.append({
                    "page": page_num,
                    "error": str(e),
                    "cached": False
                })

        total_duration = sum(p.get("duration", 0) for p in page_results)
        successful_pages = len([p for p in page_results if "error" not in p])

        return page_results, total_duration, successful_pages

    # ========================================================================
    # Error Handling
    # ========================================================================

    def _handle_error(
        self,
        state: WorkflowState,
        step_name: str,
        error: str
    ) -> WorkflowState:
        """
        Handle errors in a consistent way.

        Args:
            state: Current workflow state
            step_name: Name of the failing step
            error: Error message

        Returns:
            Updated state with error recorded
        """
        log(f"❌ Error in {step_name}: {error}")

        return {
            **state,
            "errors": state.get("errors", []) + [f"{step_name}: {error}"]
        }

    # ========================================================================
    # Public API
    # ========================================================================

    async def run_workflow(
        self,
        text: str,
        user_name: str,
        book_title: str,
        book_id: str,
        book_dir: str
    ) -> Dict[str, Any]:
        """
        Execute the complete workflow.

        This is the main entry point for the workflow.

        Args:
            text: Full text to process
            user_name: User identifier
            book_title: Book title
            book_id: Unique book identifier
            book_dir: Output directory for music files

        Returns:
            WorkflowResult dictionary with all results and metrics
        """
        log("🚀 Starting refactored LangGraph workflow")
        workflow_start = time.time()

        # Initialize state
        initial_state = WorkflowState(
            text=text,
            user_name=user_name,
            book_title=book_title,
            book_id=book_id,
            book_dir=book_dir,
            physical_chunks=[],
            emotion_analyses=[],
            final_chunks=[],
            chunk_metadata=[],
            page_chunk_mapping={},
            page_results=[],
            total_duration=0,
            successful_pages=0,
            processing_times={},
            errors=[]
        )

        # Execute workflow
        final_state = await self.graph.ainvoke(initial_state)

        # Calculate total time
        total_time = time.time() - workflow_start

        log(f"🎉 Workflow complete in {total_time:.2f}s")
        self._log_performance_summary(final_state["processing_times"])

        # Build result
        return {
            "message": f"{book_title} 음악 생성 완료 (Refactored)",
            "book_id": book_id,
            "text_length": len(text),
            "total_pages": len(final_state.get("page_chunk_mapping", {})),
            "total_chunks": len(final_state.get("chunk_metadata", [])),
            "total_duration": final_state.get("total_duration", 0),
            "successful_pages": final_state.get("successful_pages", 0),
            "pages": final_state.get("page_results", []),
            "processing_method": "langgraph_refactored",
            "processing_times": final_state.get("processing_times", {}),
            "total_time": total_time,
            "errors": final_state.get("errors", [])
        }

    def _log_performance_summary(self, times: Dict[str, float]) -> None:
        """Log a summary of performance metrics."""
        log("\n📊 Performance Summary:")
        log("=" * 50)
        for step, duration in times.items():
            log(f"   {step:20s}: {duration:6.2f}s")
        log("=" * 50)
        log(f"   {'TOTAL':20s}: {sum(times.values()):6.2f}s\n")


# ============================================================================
# Factory Function
# ============================================================================

def create_workflow(
    emotion_service: Optional[EmotionAnalysisService] = None,
    music_generator=None,
    database_service=None
) -> MusicGenerationWorkflowRefactored:
    """
    Factory function for creating workflow instances.

    Enables dependency injection for testing.

    Args:
        emotion_service: Custom emotion analysis service
        music_generator: Custom music generation service
        database_service: Custom database service

    Returns:
        Configured workflow instance
    """
    return MusicGenerationWorkflowRefactored(
        emotion_service=emotion_service,
        music_generator=music_generator,
        database_service=database_service
    )


# Singleton for production use
music_workflow_refactored = create_workflow()
