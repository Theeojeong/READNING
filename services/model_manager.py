"""모델 관리자 - 싱글톤 패턴으로 모델 재사용"""
from langchain_ollama import ChatOllama
from audiocraft.models import MusicGen
from typing import Optional
from utils.logger import log
from config import MODEL_NAME, GEN_DURATION


class OllamaManager:
    """Ollama 연결 관리 싱글톤 (langchain_ollama 사용)"""
    _instance: Optional['OllamaManager'] = None
    _llm: Optional[ChatOllama] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_llm(self) -> ChatOllama:
        """Langchain Ollama LLM 반환 (연결 재사용)"""
        if self._llm is None:
            try:
                self._llm = ChatOllama(
                    model=MODEL_NAME,
                    temperature=0.7,
                    num_ctx=4096,  # 컨텍스트 길이
                    timeout=120.0,  # 타임아웃 설정
                )
                log("Langchain Ollama LLM 초기화 완료")
            except Exception as e:
                log(f"Langchain Ollama LLM 초기화 실패: {e}")
                raise
        return self._llm
    
    def chat(self, messages: list) -> dict:
        """채팅 요청 (langchain_ollama 사용)"""
        llm = self.get_llm()
        try:
            # langchain_ollama는 메시지 리스트를 직접 받음
            response = llm.invoke(messages)
            return {
                "message": {
                    "content": response.content
                }
            }
        except Exception as e:
            log(f"LLM 채팅 요청 실패: {e}")
            raise
    
    def chat_with_structured_output(self, messages: list, response_schema) -> dict:
        """Structured Output을 사용한 채팅 요청"""
        llm = self.get_llm()
        try:
            # Pydantic 모델을 사용한 structured output
            structured_llm = llm.with_structured_output(response_schema)
            response = structured_llm.invoke(messages)
            return response
        except Exception as e:
            log(f"Structured Output LLM 요청 실패: {e}")
            raise


class MusicGenManager:
    """MusicGen 모델 관리 싱글톤"""
    _instance: Optional['MusicGenManager'] = None
    _model: Optional[MusicGen] = None
    _sample_rate: Optional[int] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(self) -> MusicGen:
        """MusicGen 모델 반환 (로드 시간 절약)"""
        if self._model is None:
            log("MusicGen 모델 로딩 중...")
            self._model = MusicGen.get_pretrained('facebook/musicgen-melody')
            self._model.set_generation_params(duration=GEN_DURATION)
            self._sample_rate = self._model.sample_rate
            log("MusicGen 모델 로딩 완료")
        return self._model
    
    @property
    def sample_rate(self) -> int:
        """샘플레이트 반환"""
        if self._sample_rate is None:
            self.get_model()
        return self._sample_rate


# 싱글톤 인스턴스 생성
ollama_manager = OllamaManager()
musicgen_manager = MusicGenManager()