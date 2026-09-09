"""Utility for reading PDF files cleanly without external services."""

import re
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader


def clean_pdf_text(text: str) -> str:
    """Clean and decode PDF text, converting CID font hex tokens (/uniXXXX) into Unicode text,
    stripping unmapped glyph tokens (/gXXXX), PUA symbols (⌂), legacy gazette header noise,
    and normalizing whitespace.
    """
    if not text:
        return ""

    # 1. Decode /uniXXXX hex tokens to actual Unicode characters
    def decode_uni(match):
        try:
            return chr(int(match.group(1), 16))
        except Exception:
            return ""

    text = re.sub(r'/uni([0-9A-Fa-f]{4})', decode_uni, text)
    text = re.sub(r'/g[0-9A-Fa-f]+', ' ', text)
    text = re.sub(r'/[a-zA-Z0-9]+', ' ', text)

    # 2. Strip PUA font artifacts (like ⌂) and unicode noise symbols
    text = re.sub(r'[⌂\u2302\u2300-\u23ff\uf000-\uf8ff\ud800-\udfff]', '', text)

    # 3. Strip Kruti Dev / Devlys font gibberish words & gazette legal header boilerplate
    legacy_words = [
        r'jftLV[^\s]*', r'laö', r'Mhö', r',yö[^\s]*', r'vlk', r'Hkkx', r'\[k\.M', r'mi&\[k\.M',
        r'izkf[^\s]*', r'c`gLIifrokj', r'fnLEcj', r'vxzgk;n[^\s]*', r'7147 GI/\d+',
        r'REGD\.\s*NO\.[^\s]*', r'EXTRAORDINARY', r'PUBLISHED BY AUTHORITY',
        r'PART II—Section 3—Sub-section \(ii\)', r'THE GAZETTE OF INDIA : EXTRAORDINARY',
        r'\[P ART II—S EC \. 3\(ii\)\]', r'NEW DELHI, THURSDAY, DECEMBER \d+, \d+',
        r'AGRAHAYANA \d+, \d+'
    ]
    for pattern in legacy_words:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)

    # 4. Remove word repeat loops: e.g. "म म म म" -> "म", "सं या सं या सं या" -> "सं या"
    text = re.sub(r'(\b[^\s]+\b)(?:\s+\1){2,}', r'\1', text)
    text = re.sub(r'(\b[^\s]+\s+[^\s]+\b)(?:\s+\1){2,}', r'\1', text)

    # 5. Normalize dot repetitions like ". . . ." into "."
    text = re.sub(r'(?:\.\s*){2,}', '... ', text)

    # 6. Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_relevant_snippet(text: str, query: str = "", max_len: int = 350) -> str:
    """Extract a crisp, clean excerpt focusing on Indian Standards and relevant answer text."""
    cleaned = clean_pdf_text(text)
    if not cleaned:
        return ""

    # If document contains Indian Standard references (IS / आई एस), extract standards clauses
    standards_matches = re.findall(
        r'(?:आई एस|IS)\s*\d+.*?(?=(?:आई एस|IS|\Z))', cleaned, re.IGNORECASE
    )
    if standards_matches:
        snippet = " | ".join([m.strip() for m in standards_matches[:4]])
        if len(snippet) > max_len:
            snippet = snippet[:max_len] + "..."
        return snippet

    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract page text and metadata from a PDF file."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages_content = []

    for idx, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        cleaned_text = clean_pdf_text(raw_text)
        pages_content.append({
            "page_number": idx + 1,
            "text": cleaned_text
        })

    return pages_content