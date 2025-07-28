"""모델 관리자 - 싱글톤 패턴으로 모델 재사용"""
import ollama
from audiocraft.models import MusicGen
from typing import Optional
from utils.logger import log
from config import MODEL_NAME, GEN_DURATION


class OllamaManager:
    """Ollama 연결 관리 싱글톤"""
    _instance: Optional['OllamaManager'] = None
    _client: Optional[object] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        """올라마 클라이언트 반환 (연결 재사용)"""
        if self._client is None:
            try:
                self._client = ollama
                log("Ollama 클라이언트 초기화 완료")
            except Exception as e:
                log(f"Ollama 클라이언트 초기화 실패: {e}")
                raise
        return self._client
    
    def chat(self, messages: list) -> dict:
        """채팅 요청 (재시도 로직 포함)"""
        client = self.get_client()
        return client.chat(model=MODEL_NAME, messages=messages)


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