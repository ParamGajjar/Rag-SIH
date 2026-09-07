import os
import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from backend.app.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentMetadata,
    DeleteDocumentResponse
)
from backend.app.services.ingestion import (
    validate_and_read_pdf,
    save_pdf_to_disk,
    load_pdf_pages_from_file,
    chunk_pdf_pages
)
from backend.app.services.embedding import EmbeddingManager
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.document_store import document_registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Lazy service singletons
embedding_manager = EmbeddingManager()
vectorstore_manager = VectorStoreManager()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_200_OK)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload, validate, chunk, embed, and store a PDF document with SHA-256 deduplication.
    """
    # 1. Validate file format, size, and compute SHA-256 hash
    clean_filename, content_bytes, file_hash = validate_and_read_pdf(file)

    # 2. Check for duplicate upload
    existing_doc = document_registry.get_by_hash(file_hash)
    if existing_doc:
        logger.info(f"Duplicate document detected (hash: {file_hash[:8]}). Returning existing entry.")
        return DocumentUploadResponse(
            document_id=existing_doc["document_id"],
            filename=existing_doc["filename"],
            status="ready",
            page_count=existing_doc["page_count"],
            total_chunks=existing_doc["total_chunks"],
            file_hash=file_hash,
            is_duplicate=True
        )

    # 3. Process new document
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    logger.info(f"Processing new PDF upload: {clean_filename} (ID: {document_id})")

    # 4. Save file to disk
    stored_path = save_pdf_to_disk(clean_filename, content_bytes, document_id)

    try:
        # 5. Extract pages
        pages = load_pdf_pages_from_file(stored_path, clean_filename)
        page_count = len(pages)

        # 6. Chunk text with metadata
        chunks = chunk_pdf_pages(pages, document_id, clean_filename)
        total_chunks = len(chunks)

        # 7. Generate embeddings
        texts = [c.page_content for c in chunks]
        embeddings = embedding_manager.generate_embeddings(texts)

        # 8. Add to ChromaDB vector store
        vectorstore_manager.add_documents(chunks, embeddings)

        # 9. Register document metadata
        doc_metadata = {
            "document_id": document_id,
            "filename": clean_filename,
            "stored_path": stored_path,
            "upload_time": datetime.utcnow().isoformat(),
            "page_count": page_count,
            "total_chunks": total_chunks,
            "file_size": len(content_bytes),
            "file_hash": file_hash
        }
        document_registry.save_document(doc_metadata)

        return DocumentUploadResponse(
            document_id=document_id,
            filename=clean_filename,
            status="ready",
            page_count=page_count,
            total_chunks=total_chunks,
            file_hash=file_hash,
            is_duplicate=False
        )

    except Exception as e:
        logger.error(f"Error processing document upload {clean_filename}: {e}", exc_info=True)
        # Clean up file on failure
        if os.path.exists(stored_path):
            try:
                os.remove(stored_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
def list_documents():
    """List all indexed documents and metadata"""
    docs_data = document_registry.list_documents()
    documents = [DocumentMetadata(**doc) for doc in docs_data]
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse, status_code=status.HTTP_200_OK)
def delete_document(document_id: str):
    """
    Delete indexed document: remove metadata, stored PDF file, and ChromaDB vector entries.
    """
    doc = document_registry.get_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    filename = doc.get("filename", document_id)
    stored_path = doc.get("stored_path")

    # 1. Remove vectors from ChromaDB
    try:
        vectorstore_manager.delete_document_vectors(document_id)
    except Exception as e:
        logger.warning(f"Error deleting vectors for {document_id}: {e}")

    # 2. Delete file from disk
    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
            logger.info(f"Deleted PDF file from disk: {stored_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {stored_path}: {e}")

    # 3. Remove metadata from registry
    document_registry.delete_document(document_id)

    return DeleteDocumentResponse(
        message=f"Document '{filename}' and associated vector entries successfully deleted.",
        document_id=document_id
    )
