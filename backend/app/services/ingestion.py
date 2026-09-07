import os
import uuid
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from backend.app.config import settings

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and unsafe characters"""
    # Extract basename only
    base_name = Path(filename).name
    # Replace non-alphanumeric (except dots, underscores, dashes) with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name)
    if not clean_name.lower().endswith('.pdf'):
        clean_name += '.pdf'
    return clean_name


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA-256 hash of byte content"""
    return hashlib.sha256(content).hexdigest()


def validate_and_read_pdf(file: UploadFile) -> Tuple[str, bytes, str]:
    """
    Validate uploaded file: check format, file size, and compute SHA-256 hash.
    
    Returns:
        Tuple of (clean_filename, content_bytes, file_hash)
    """
    filename = file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )

    clean_name = sanitize_filename(filename)
    
    # Read file bytes
    try:
        content = file.file.read()
    except Exception as e:
        logger.error(f"Failed to read file content: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file."
        )

    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Check max file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Validate PDF magic header (%PDF)
    if not content.startswith(b'%PDF'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is not a valid PDF document."
        )

    file_hash = calculate_sha256(content)
    return clean_name, content, file_hash


def save_pdf_to_disk(clean_filename: str, content: bytes, document_id: str) -> str:
    """Save PDF file bytes safely to storage directory"""
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    stored_filename = f"{document_id}_{clean_filename}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, stored_filename)
    
    with open(file_path, 'wb') as f:
        f.write(content)
        
    logger.info(f"Saved PDF to disk: {file_path}")
    return file_path


def load_pdf_pages_from_file(file_path: str, filename: str) -> List[Document]:
    """Load PDF page-by-page, preserving 1-indexed page numbers"""
    try:
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
    except Exception as e:
        logger.error(f"Error parsing PDF file {file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF document: {str(e)}"
        )

    if not raw_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF document contains no readable text pages."
        )

    processed_pages = []
    for i, doc in enumerate(raw_docs):
        # Ensure 1-indexed page number
        page_num = doc.metadata.get('page', i) + 1 if 'page' in doc.metadata else (i + 1)
        doc.metadata['page'] = page_num
        doc.metadata['source'] = filename
        doc.metadata['filename'] = filename
        processed_pages.append(doc)

    logger.info(f"Successfully loaded {len(processed_pages)} pages from {filename}")
    return processed_pages


def chunk_pdf_pages(documents: List[Document], document_id: str, filename: str) -> List[Document]:
    """
    Split document pages into chunks, attaching comprehensive metadata to every chunk:
    - document_id
    - filename
    - page
    - chunk_id
    - source
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=90,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    raw_chunks = text_splitter.split_documents(documents)
    enhanced_chunks = []
    
    for idx, chunk in enumerate(raw_chunks):
        chunk_id = f"{document_id}_chunk_{idx+1}"
        page_num = chunk.metadata.get('page', 1)
        
        chunk.metadata.update({
            "document_id": document_id,
            "filename": filename,
            "page": page_num,
            "chunk_id": chunk_id,
            "source": filename
        })
        enhanced_chunks.append(chunk)
        
    logger.info(f"Created {len(enhanced_chunks)} chunks for document {document_id}")
    return enhanced_chunks


def process_all_pdfs(pdf_directory: str) -> List[Document]:
    """Legacy helper for backward compatibility"""
    all_documents = []
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists():
        return []
    for pdf_file in pdf_dir.glob("**/*.pdf"):
        try:
            docs = load_pdf_pages_from_file(str(pdf_file), pdf_file.name)
            all_documents.extend(docs)
        except Exception:
            pass
    return all_documents


def split_documents(documents: List[Document], chunk_size: int = 400, chunk_overlap: int = 90) -> List[Document]:
    """Legacy helper for backward compatibility"""
    return chunk_pdf_pages(documents, document_id=uuid.uuid4().hex[:8], filename="document.pdf")
