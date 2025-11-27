"""모델 관리자 - 싱글톤 패턴으로 모델 재사용"""
import ollama
from audiocraft.models import MusicGen
from typing import Optional, Type
from utils.logger import log
from config import MODEL_NAME, GEN_DURATION
from langchain_ollama import ChatOllama
from pydantic import BaseModel


from langchain_openai import ChatOpenAI
from openai import OpenAI
from config import OPENAI_API_KEY

class OpenAIManager:
    """OpenAI 연결 관리 싱글톤"""
    _instance: Optional['OpenAIManager'] = None
    _lc_llm: Optional[ChatOpenAI] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        if not hasattr(self, '_initialized'):
            try:
                if not OPENAI_API_KEY:
                    log("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
                else:
                    log(f"✅ OpenAI 모델 {MODEL_NAME} 사용 준비 완료")
                
                self._initialized = True
            except Exception as e:
                log(f"OpenAI 초기화 실패: {e}")
                self._initialized = True
    
    def chat(self, messages: list) -> dict:
        """채팅 요청 (직접 OpenAI API 사용)"""
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7,
            )
            return {
                "message": {
                    "content": response.choices[0].message.content
                }
            }
        except Exception as e:
            log(f"LLM 채팅 요청 실패: {e}")
            log("⚠️ OpenAI 연결 실패. 기본 응답을 반환합니다.")
            return {
                "message": {
                    "content": "Scene Summary: A calm and neutral atmosphere.\nMusic Description: Gentle piano music with a slow tempo."
                }
            }
    
    def _get_langchain_llm(self) -> ChatOpenAI:
        """LangChain ChatOpenAI 인스턴스 (지연 생성, 재사용)."""
        if self._lc_llm is None:
            self._lc_llm = ChatOpenAI(
                model=MODEL_NAME,
                temperature=0.7,
                api_key=OPENAI_API_KEY
            )
            log("LangChain ChatOpenAI 초기화 완료")
        return self._lc_llm

    def chat_with_structured_output(self, messages: list, response_schema: Type[BaseModel]) -> dict:
        """LangChain Structured Output로 응답을 받아 Pydantic dict 반환."""
        try:
            llm = self._get_langchain_llm()
            structured_llm = llm.with_structured_output(response_schema)
            result_model = structured_llm.invoke(messages)  # Pydantic 모델 인스턴스
            return result_model.model_dump()
        except Exception as e:
            log(f"Structured Output 요청 실패: {e}")
            log("⚠️ OpenAI 연결 실패. 기본 구조화된 응답을 반환합니다.")
            return {
                "emotional_tone": "Neutral",
                "music_prompt": "Ambient background music, calm and steady.",
                "confidence": 0.5
            }


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
        """MusicGen 모델 반환 (싱글톤 보장)"""
        if self._model is None:
            log("🎵 MusicGen 모델 로딩 중... (싱글톤)")
            try:
                self._model = MusicGen.get_pretrained('facebook/musicgen-melody')
                self._model.set_generation_params(duration=GEN_DURATION)
                self._sample_rate = self._model.sample_rate
                log("✅ MusicGen 모델 로딩 완료")
            except Exception as e:
                log(f"❌ MusicGen 모델 로딩 실패: {e}")
                raise
        return self._model
    
    @property
    def sample_rate(self) -> int:
        """샘플레이트 반환"""
        if self._sample_rate is None:
            self.get_model()
        return self._sample_rate


# 싱글톤 인스턴스 생성
ollama_manager = OpenAIManager()
musicgen_manager = MusicGenManager()