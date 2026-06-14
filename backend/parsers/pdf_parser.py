import base64
import io

from backend.config import utc_now
from pypdf import PdfReader


def parse_pdf(base64_content: str) -> str:
    start = utc_now()
    pdf_bytes = base64.b64decode(base64_content)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if not extracted:
            extracted = page.extract_text(extraction_mode="layout") or ""
        text += extracted
    elapsed = (utc_now() - start).total_seconds()
    if not text.strip():
        return (
            f"[{utc_now().isoformat()}] PDF appears to be scanned. "
            f"Text extraction failed after {elapsed:.1f}s. "
            "Consider running OCR on this file."
        )
    return text.strip()


def get_pdf_metadata(base64_content: str) -> dict:
    pdf_bytes = base64.b64decode(base64_content)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    metadata = reader.metadata

    return {
        "pages": len(reader.pages),
        "title": (metadata.title if metadata and metadata.title else ""),
        "author": (metadata.author if metadata and metadata.author else ""),
        "extracted_at": utc_now().isoformat(),
    }
