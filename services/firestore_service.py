import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

"""
Firestore 의존성을 자동으로 우회하도록 개선한 버전.

▪ DISABLE_FIRESTORE=1   → 강제 더미 모드
▪ GOOGLE_APPLICATION_CREDENTIALS & FIREBASE_BUCKET 둘 다 없을 때 → 경고만 남기고 더미 모드로 전환
   (더 이상 RuntimeError 를 발생시키지 않음)
"""

# ──────────────────────────────────────────────────────────────
# 1) .env 로드 및 환경변수 검사
# ──────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

ENV_DISABLE      = os.getenv("DISABLE_FIRESTORE", "0") == "1"
SA_PATH: Optional[str]     = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME: Optional[str] = os.getenv("FIREBASE_BUCKET")  # ex) readning.appspot.com

# Firebase 사용 여부 결정
USE_FIREBASE = (not ENV_DISABLE) and SA_PATH and BUCKET_NAME

if USE_FIREBASE:
    # ──────────────────────────────────────────────────────────
    # 2) Firebase App 초기화 (한 번만)
    # ──────────────────────────────────────────────────────────
    import firebase_admin
    from firebase_admin import credentials, firestore, storage

    if not firebase_admin._apps:
        cred = credentials.Certificate(SA_PATH)  # type: ignore[arg-type]
        firebase_admin.initialize_app(cred, {"storageBucket": BUCKET_NAME})

    _db     = firestore.client()
    _bucket = storage.bucket()  # 기본 버킷 설정 완료
else:
    # ──────────────────────────────────────────────────────────
    # 3) Firebase 없이 실행하는 더미 구현체
    # ──────────────────────────────────────────────────────────
    if not ENV_DISABLE:
        # 사용자 실수로 자격증명이 빠진 경우라도 서버가 죽지 않도록 경고만 출력
        print("[firestore_service] WARNING: Firebase 자격증명/버킷이 누락되어 더미 모드로 전환합니다.")

    class _DummyDoc:
        exists: bool = False
        def to_dict(self) -> None:  # type: ignore[override]
            return None

    class _DummyCollection:
        def document(self, *a: Any, **kw: Any) -> "_DummyCollection":
            return self
        def collection(self, *a: Any, **kw: Any) -> "_DummyCollection":
            return self
        def set(self, *a: Any, **kw: Any) -> None:
            pass
        def get(self) -> "_DummyDoc":
            return _DummyDoc()

    class _DummyBucket:
        class _DummyBlob:
            public_url: str = ""
            def upload_from_filename(self, *a: Any, **kw: Any) -> None:
                pass
            def make_public(self) -> None:
                pass
        def blob(self, *a: Any, **kw: Any) -> "_DummyBucket._DummyBlob":
            return self._DummyBlob()

    _db     = _DummyCollection()
    _bucket = _DummyBucket()

# ──────────────────────────────────────────────────────────────
# 4) 공통 유틸 함수 (Firebase 유무와 무관)
# ──────────────────────────────────────────────────────────────

def add_book_info(uid: str, book_id: str, data: Dict[str, Any]) -> None:
    """users/{uid}/books/{book_id} 문서에 책 정보 추가·병합"""
    _db.collection("users").document(uid) \
       .collection("books").document(book_id) \
       .set(data, merge=True)


def get_book_info(uid: str, book_id: str) -> Optional[Dict[str, Any]]:
    """users/{uid}/books/{book_id} 문서 가져오기"""
    doc = (
        _db.collection("users").document(uid)
           .collection("books").document(book_id)
           .get()
    )
    return doc.to_dict() if getattr(doc, "exists", False) else None


def upload_audio(path: str) -> str:
    """파일을 Firebase Storage(또는 더미)에 업로드하고 public URL 반환"""
    blob = _bucket.blob(os.path.basename(path))
    blob.upload_from_filename(path)  # 더미 모드면 no-op
    blob.make_public()               # 더미 모드면 no-op
    return blob.public_url
