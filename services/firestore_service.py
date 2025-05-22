import os
from pathlib import Path

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage

# ──────────────────────────────────────────────────────────────
# 1) .env 로드 (GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_BUCKET)
# ──────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SA_PATH     = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("FIREBASE_BUCKET")        # ex) readning-3cb46.appspot.com

if not SA_PATH or not BUCKET_NAME:
    raise RuntimeError(
        "환경변수 설정 누락\n"
        " - GOOGLE_APPLICATION_CREDENTIALS: 서비스 계정 키 JSON 절대경로\n"
        " - FIREBASE_BUCKET           : Firebase Storage 기본 버킷명"
    )

# ──────────────────────────────────────────────────────────────
# 2) Firebase App 초기화 (한 번만)
# ──────────────────────────────────────────────────────────────
if not firebase_admin._apps:
    cred = credentials.Certificate(SA_PATH)
    firebase_admin.initialize_app(cred, {"storageBucket": BUCKET_NAME})

_db     = firestore.client()
_bucket = storage.bucket()        # 기본 버킷이 설정됐으므로 이름 생략 OK

# ──────────────────────────────────────────────────────────────
# 3) Firestore & Storage 유틸 함수
# ──────────────────────────────────────────────────────────────
def add_book_info(book_id: str, data: dict) -> None:
    """Add or update book information in Firestore."""
    _db.collection("books").document(book_id).set(data, merge=True)


def get_book_info(book_id: str) -> dict | None:
    """Retrieve book information from Firestore."""
    doc = _db.collection("books").document(book_id).get()
    return doc.to_dict() if doc.exists else None


def upload_audio(path: str) -> str:
    """Upload a file to Firebase Storage and return its public URL."""
    blob = _bucket.blob(os.path.basename(path))
    blob.upload_from_filename(path)
    blob.make_public()
    return blob.public_url
