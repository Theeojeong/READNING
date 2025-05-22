import os

import firebase_admin
from firebase_admin import credentials, firestore, storage


# Initialize Firebase app using service account credentials on first import
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    )

_db = firestore.client()
_bucket = storage.bucket()


def add_book_info(book_id: str, data: dict) -> None:
    """Add or update book information in Firestore."""
    _db.collection("books").document(book_id).set(data, merge=True)


def get_book_info(book_id: str) -> dict | None:
    """Retrieve book information from Firestore."""
    doc = _db.collection("books").document(book_id).get()
    return doc.to_dict() if doc.exists else None


def upload_audio(path: str) -> str:
    """Upload a WAV file to Firebase Storage and return its public URL."""
    blob = _bucket.blob(os.path.basename(path))
    blob.upload_from_filename(path)
    blob.make_public()
    return blob.public_url
