import os

import firebase_admin
from firebase_admin import credentials, firestore, storage

# Initialize Firebase app once using service account credentials
_cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if not firebase_admin._apps:
    if not _cred_path or not os.path.exists(_cred_path):
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS env var must point to a service account key"
        )
    cred = credentials.Certificate(_cred_path)
    options = {}
    bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")
    if bucket_name:
        options["storageBucket"] = bucket_name
    firebase_admin.initialize_app(cred, options)

_db = firestore.client()
_bucket = storage.bucket() if firebase_admin.get_app().project_id else None


def add_book_info(book_id: str, data: dict) -> None:
    """Add or update book information in Firestore."""
    _db.collection("books").document(book_id).set(data, merge=True)


def get_book_info(book_id: str) -> dict | None:
    """Retrieve book information from Firestore."""
    doc = _db.collection("books").document(book_id).get()
    return doc.to_dict() if doc.exists else None


def upload_audio(file_path: str, dest_path: str) -> str:
    """Upload an audio file to Firebase Storage and return its public URL."""
    if _bucket is None:
        raise RuntimeError("Firebase Storage bucket is not configured")
    blob = _bucket.blob(dest_path)
    blob.upload_from_filename(file_path)
    blob.make_public()
    return blob.public_url
