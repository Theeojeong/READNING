import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 1) .env 로드
#    - DISABLE_FIRESTORE=1 이면 Firebase 의존성을 모두 우회합니다.
#    - 그렇지 않으면 GOOGLE_APPLICATION_CREDENTIALS와 FIREBASE_BUCKET을 사용합니다.
# ──────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

DISABLE_FIRESTORE = os.getenv("DISABLE_FIRESTORE", "0") == "1"

if not DISABLE_FIRESTORE:
    # Firebase 사용 모드
    SA_PATH: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    BUCKET_NAME: Optional[str] = os.getenv("FIREBASE_BUCKET")  # ex) readning.appspot.com

    if not SA_PATH or not BUCKET_NAME:
        raise RuntimeError(
            "환경변수 설정 누락\n"
            " - GOOGLE_APPLICATION_CREDENTIALS: 서비스 계정 키 JSON 절대경로\n"
            " - FIREBASE_BUCKET           : Firebase Storage 기본 버킷명\n"
        )

    import firebase_admin
    from firebase_admin import credentials, firestore, storage

    # ──────────────────────────────────────────────────────────
    # 2) Firebase App 초기화 (한 번만)
    # ──────────────────────────────────────────────────────────
    if not firebase_admin._apps:
        cred = credentials.Certificate(SA_PATH)
        firebase_admin.initialize_app(cred, {"storageBucket": BUCKET_NAME})

    _db = firestore.client()
    _bucket = storage.bucket()  # 기본 버킷이 설정됐으므로 이름 생략 OK

else:
    # Firebase 없이 실행하는 더미 모드
    class _DummyDoc:
        exists: bool = False
        def to_dict(self) -> None:
            return None

    class _DummyCollection:
        def document(self, *a: Any, **kw: Any) -> "_DummyCollection":
            return self
        def collection(self, *a: Any, **kw: Any) -> "_DummyCollection":
            return self
        def set(self, *a: Any, **kw: Any) -> None:
            pass
        def get(self) -> _DummyDoc:  # type: ignore[name-defined]
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

    _db = _DummyCollection()
    _bucket = _DummyBucket()

# ──────────────────────────────────────────────────────────────
# 3) Firestore & Storage 유틸 함수 (Firebase 유무에 상관없이 동일 인터페이스 보장)
# ──────────────────────────────────────────────────────────────

def add_book_info(uid: str, book_id: str, data: Dict[str, Any]) -> None:
    """users/{uid}/books/{book_id} 문서에 책 정보 추가·병합"""
    _db.collection("users").document(uid) \
       .collection("books").document(book_id) \
       .set(data, merge=True)


def get_book_info(uid: str, book_id: str) -> Optional[Dict[str, Any]]:
    """users/{uid}/books/{book_id} 문서 가져오기"""
    doc = (_db.collection("users").document(uid)
                 .collection("books").document(book_id)
                 .get())
    return doc.to_dict() if getattr(doc, "exists", False) else None


def upload_audio(path: str) -> str:
    """파일을 Firebase Storage(또는 더미)로 업로드하고 public URL 반환"""
    blob = _bucket.blob(os.path.basename(path))
    # 실제 Firebase 모드에서는 업로드 진행, 더미 모드는 no‑op
    blob.upload_from_filename(path)
    blob.make_public()
    return blob.public_url
