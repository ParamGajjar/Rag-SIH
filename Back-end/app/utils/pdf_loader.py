"""Utility for reading PDF files cleanly without external services."""

from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader

def extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract page text and metadata from a PDF file.
    
    Returns a list of dicts: [{'page': 1, 'text': '...'}, ...]
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages_content = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_content.append({
            "page_number": idx + 1,
            "text": text.strip()
        })

    return pages_content