"""
PDF Document Ingestion & Text Extraction Service.
Extracts structured text and metadata from lecture slides and course documents.
"""

import io
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class InvalidPdfError(ValueError):
    """Raised when uploaded bytes are empty or not a readable PDF."""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Parses a PDF file from bytes and extracts all clean text along with page metadata.
    """
    if not pdf_bytes:
        raise InvalidPdfError("Uploaded file is empty")
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except PdfReadError as e:
        raise InvalidPdfError(f"Could not read PDF: {e}") from e
    page_count = len(reader.pages)
    extracted_pages = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        cleaned = text.strip()
        if cleaned:
            extracted_pages.append(f"--- Page {idx + 1} ---\n{cleaned}")

    full_text = "\n\n".join(extracted_pages)
    return {
        "page_count": page_count,
        "content": full_text if full_text.strip() else "No readable text found in document.",
        "has_content": len(extracted_pages) > 0
    }


def create_sample_pdf_bytes(title: str, text: str) -> bytes:
    """Helper for testing: creates a minimal valid PDF document in memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
