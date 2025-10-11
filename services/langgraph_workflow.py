import asyncio
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from services.split_text import split_text_with_sliding_window
from services.model_manager import ollama_manager
from services.analyze_emotions_with_gpt import EmotionAnalysisResult, analyze_emotions_with_gpt
from services.async_music_generation import process_all_chunks_async
from services.mysql_service import mysql_service
from services import prompt_service
from utils.logger import log
from config import GEN_DURATION


class WorkflowState(TypedDict):
    """워크플로우 상태 정의"""
    # 입력 데이터
    text: str
    user_name: str
    book_title: str
    book_id: str
    book_dir: str
    
    # 중간 처리 결과
    physical_chunks: List[str]
    emotion_analyses: List[Dict[str, Any]]
    final_chunks: List[Dict[str, Any]]
    chunk_metadata: List[Dict[str, Any]]
    
    # 최종 결과
    page_chunk_mapping: Dict[int, Dict[str, Any]]
    page_results: List[Dict[str, Any]]
    total_duration: int
    successful_pages: int
    
    # 메타데이터
    processing_times: Dict[str, float]
    errors: List[str]


class MusicGenerationWorkflow:
    """LangGraph 기반 음악 생성 워크플로우"""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(WorkflowState)
        
        # 노드 추가
        workflow.add_node("split_text", self._split_text_node)
        workflow.add_node("analyze_emotions", self._analyze_emotions_node)
        workflow.add_node("create_final_chunks", self._create_final_chunks_node)
        workflow.add_node("generate_music", self._generate_music_node)
        workflow.add_node("save_to_database", self._save_to_database_node)
        workflow.add_node("create_page_mapping", self._create_page_mapping_node)
        
        # 엣지 연결
        workflow.set_entry_point("split_text")
        workflow.add_edge("split_text", "analyze_emotions")
        workflow.add_edge("analyze_emotions", "create_final_chunks")
        workflow.add_edge("create_final_chunks", "generate_music")
        workflow.add_edge("generate_music", "create_page_mapping")
        workflow.add_edge("create_page_mapping", "save_to_database")
        workflow.add_edge("save_to_database", END)
        
        return workflow.compile()
    
    async def _split_text_node(self, state: WorkflowState) -> WorkflowState:
        """1단계: 텍스트를 물리적 청크로 분리"""
        import time
        start_time = time.time()
        
        log("📖 LangGraph: 텍스트 분리 시작")
        
        try:
            # 슬라이딩 윈도우로 텍스트 분리
            physical_chunks = split_text_with_sliding_window(
                state["text"], 
                max_size=6000, 
                overlap=600
            )
            
            elapsed_time = time.time() - start_time
            log(f"✅ LangGraph: 텍스트 분리 완료 - {len(physical_chunks)}개 청크 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "physical_chunks": physical_chunks,
                "processing_times": {**state.get("processing_times", {}), "split_text": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: 텍스트 분리 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"텍스트 분리 실패: {e}"]
            }
    
    async def _analyze_emotions_node(self, state: WorkflowState) -> WorkflowState:
        """2단계: 모든 청크를 비동기로 감정 분석"""
        import time
        start_time = time.time()
        
        log(f"🎭 LangGraph: {len(state['physical_chunks'])}개 청크 감정 분석 시작")
        
        try:
            # 글로벌 프롬프트 생성
            global_prompt = prompt_service.generate_global(state["text"])
            
            # 모든 청크를 비동기로 감정 분석
            emotion_analyses = []
            for i, chunk in enumerate(state["physical_chunks"]):
                try:
                    # 기존 analyze_emotions_with_gpt 함수 사용
                    result = analyze_emotions_with_gpt(chunk)
                    
                    emotion_analyses.append({
                        "chunk_index": i,
                        "text": chunk,
                        "analysis": result,
                        "success": True
                    })
                    
                except Exception as e:
                    log(f"❌ 청크 {i} 감정 분석 실패: {e}")
                    emotion_analyses.append({
                        "chunk_index": i,
                        "text": chunk,
                        "error": str(e),
                        "success": False
                    })
            
            elapsed_time = time.time() - start_time
            successful_count = len([a for a in emotion_analyses if a["success"]])
            log(f"✅ LangGraph: 감정 분석 완료 - 성공 {successful_count}/{len(emotion_analyses)}개 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "emotion_analyses": emotion_analyses,
                "processing_times": {**state.get("processing_times", {}), "analyze_emotions": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: 감정 분석 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"감정 분석 실패: {e}"]
            }
    
    async def _create_final_chunks_node(self, state: WorkflowState) -> WorkflowState:
        """3단계: 감정 분석 결과를 기반으로 최종 청크 생성"""
        import time
        start_time = time.time()
        
        log("✂️ LangGraph: 최종 청크 생성 시작")
        
        try:
            final_chunks = []
            for analysis in state["emotion_analyses"]:
                if analysis["success"]:
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
            log(f"✅ LangGraph: 최종 청크 생성 완료 - {len(final_chunks)}개 청크 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "final_chunks": final_chunks,
                "processing_times": {**state.get("processing_times", {}), "create_final_chunks": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: 최종 청크 생성 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"최종 청크 생성 실패: {e}"]
            }
    
    async def _generate_music_node(self, state: WorkflowState) -> WorkflowState:
        """4단계: 모든 청크를 비동기로 음악 생성"""
        import time
        start_time = time.time()
        
        log(f"🎵 LangGraph: {len(state['final_chunks'])}개 청크 음악 생성 시작")
        
        try:
            # 글로벌 프롬프트 생성
            global_prompt = prompt_service.generate_global(state["text"])
            
            # 모든 청크를 비동기로 음악 생성
            chunk_metadata = await process_all_chunks_async(
                state["final_chunks"], 
                state["book_dir"], 
                global_prompt
            )
            
            elapsed_time = time.time() - start_time
            log(f"✅ LangGraph: 음악 생성 완료 - {len(chunk_metadata)}개 성공 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "chunk_metadata": chunk_metadata,
                "processing_times": {**state.get("processing_times", {}), "generate_music": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: 음악 생성 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"음악 생성 실패: {e}"]
            }
    
    async def _create_page_mapping_node(self, state: WorkflowState) -> WorkflowState:
        """5단계: 페이지별 청크 매핑 생성"""
        import time
        start_time = time.time()
        
        log("📄 LangGraph: 페이지 매핑 생성 시작")
        
        try:
            # 페이지별 청크 매핑 생성 (한 페이지당 4개 청크 고정)
            page_chunk_mapping = {}
            CHUNKS_PER_PAGE = 4
            
            for i, chunk in enumerate(state["chunk_metadata"]):
                page_num = (i // CHUNKS_PER_PAGE) + 1
                if page_num not in page_chunk_mapping:
                    page_chunk_mapping[page_num] = {
                        "start_index": i + 1,
                        "end_index": i + 1,
                        "chunk_count": 0
                    }
                page_chunk_mapping[page_num]["end_index"] = i + 1
                page_chunk_mapping[page_num]["chunk_count"] += 1
                chunk["page"] = page_num
            
            elapsed_time = time.time() - start_time
            log(f"✅ LangGraph: 페이지 매핑 생성 완료 - {len(page_chunk_mapping)}페이지 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "page_chunk_mapping": page_chunk_mapping,
                "processing_times": {**state.get("processing_times", {}), "create_page_mapping": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: 페이지 매핑 생성 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"페이지 매핑 생성 실패: {e}"]
            }
    
    async def _save_to_database_node(self, state: WorkflowState) -> WorkflowState:
        """6단계: DB에 저장"""
        import time
        start_time = time.time()
        
        log("💾 LangGraph: DB 저장 시작")
        
        try:
            page_results = []
            
            for page_num, mapping in state["page_chunk_mapping"].items():
                start_idx = mapping["start_index"] - 1
                end_idx = mapping["end_index"]
                
                page_chunks = state["chunk_metadata"][start_idx:end_idx]
                
                if not page_chunks:
                    page_results.append({
                        "page": page_num,
                        "chunks": 0,
                        "duration": 0,
                        "error": "청크 생성 실패"
                    })
                    continue
                
                page_duration = len(page_chunks) * GEN_DURATION
                
                try:
                    mysql_service.save_chapter_chunks(
                        book_id=state["book_id"],
                        page=page_num,
                        chunks=page_chunks,
                        total_duration=page_duration,
                        book_title=state["book_title"],
                    )
                    
                    page_results.append({
                        "page": page_num,
                        "chunks": len(page_chunks),
                        "duration": page_duration,
                        "cached": False
                    })
                    
                except Exception as e:
                    page_results.append({
                        "page": page_num,
                        "error": str(e),
                        "cached": False
                    })
            
            total_duration = sum(page.get("duration", 0) for page in page_results)
            successful_pages = len([p for p in page_results if "error" not in p])
            
            elapsed_time = time.time() - start_time
            log(f"✅ LangGraph: DB 저장 완료 - {successful_pages}페이지 성공 ({elapsed_time:.2f}초)")
            
            return {
                **state,
                "page_results": page_results,
                "total_duration": total_duration,
                "successful_pages": successful_pages,
                "processing_times": {**state.get("processing_times", {}), "save_to_database": elapsed_time}
            }
            
        except Exception as e:
            log(f"❌ LangGraph: DB 저장 실패 - {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"DB 저장 실패: {e}"]
            }
    
    async def run_workflow(self, text: str, user_name: str, book_title: str, book_id: str, book_dir: str) -> Dict[str, Any]:
        """워크플로우 실행"""
        log("🚀 LangGraph 워크플로우 시작")
        
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
        
        # 워크플로우 실행
        final_state = await self.graph.ainvoke(initial_state)
        
        log("🎉 LangGraph 워크플로우 완료")
        
        return {
            "message": f"{book_title} 음악 생성 완료 (LangGraph)",
            "book_id": book_id,
            "text_length": len(text),
            "total_pages": len(final_state["page_chunk_mapping"]),
            "total_chunks": len(final_state["chunk_metadata"]),
            "total_duration": final_state["total_duration"],
            "successful_pages": final_state["successful_pages"],
            "pages": final_state["page_results"],
            "processing_method": "langgraph_workflow",
            "processing_times": final_state["processing_times"],
            "errors": final_state["errors"]
        }


# 싱글톤 인스턴스
music_workflow = MusicGenerationWorkflow()
