import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from fastapi import UploadFile, HTTPException
import io

class TextProcessingService:
    @staticmethod
    async def extract_text(file: UploadFile) -> str:
        """
        Extract text from uploaded file based on its content type or extension.
        Supports: PDF, EPUB, TXT
        """
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            return TextProcessingService._extract_from_pdf(content)
        elif filename.endswith('.epub'):
            return TextProcessingService._extract_from_epub(content)
        elif filename.endswith('.txt'):
            return content.decode('utf-8')
        else:
            # Try to decode as text if unknown, or raise error
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400, 
                    detail="Unsupported file format. Please upload PDF, EPUB, or TXT."
                )

    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text = []
            for page in doc:
                text.append(page.get_text())
            return "\n".join(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def _extract_from_epub(content: bytes) -> str:
        try:
            # ebooklib requires a file path or file-like object. 
            # We can write to a temporary file or try to use BytesIO if supported (ebooklib might be picky).
            # Writing to a temp file is safer for ebooklib.
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                book = epub.read_epub(tmp_path)
                text = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        text.append(soup.get_text())
                return "\n".join(text)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse EPUB: {str(e)}")

text_processing_service = TextProcessingService()
