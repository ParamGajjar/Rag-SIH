"""FastAPI Server for Vectorless RAG Application."""

import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import Config
from app.rag.generator import ask_question
from app.rag.indexer import index_all_documents, index_document

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="Vectorless RAG API",
    description="API for querying documents using PageIndex tree reasoning.",
    version="1.0.0"
)

# CORS Configuration
origins = [
    getattr(Config, "FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins during local dev integration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Pydantic Schemas (Request / Response Models)
# ------------------------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user query or question.", example="What is the main topic of the document?")

class ContextItem(BaseModel):
    doc_name: str = Field(..., description="Source document file name.")
    page_number: int = Field(..., description="Source page number.")
    content: str = Field(..., description="Extracted text chunk from source page.")

class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = Field(..., description="Formatted source list string.")
    context: List[ContextItem] = Field(..., description="Full context documents retrieved for the answer.")

class IndexingResponse(BaseModel):
    status: str
    indexed_files_count: int
    saved_paths: List[str]

class DocumentItem(BaseModel):
    id: str
    filename: str
    size: int
    indexed: bool

class HealthResponse(BaseModel):
    status: str = Field("ok", description="Server health status")



# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.get("/", tags=["Health"])
def get_health():
    """Health check endpoint - forced bypass returning static OK status"""
    return HealthResponse(status="ok")

@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health():
    """Health check endpoint - forced bypass returning static OK status"""
    return HealthResponse(status="ok")

@app.post("/ask", response_model=RAGResponse, status_code=status.HTTP_200_OK, tags=["RAG"])
def ask_question_endpoint(payload: QuestionRequest):
    """Submit a question to the RAG pipeline."""
    clean_question = payload.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only."
        )

    try:
        logger.info(f"Processing API question: '{clean_question}'")
        rag_result = ask_question(clean_question)

        context_items = [
            ContextItem(
                doc_name=ctx.get("doc_name", "Unknown"),
                page_number=ctx.get("page_number", 0),
                content=ctx.get("content", "")
            )
            for ctx in rag_result.get("context", [])
        ]

        return RAGResponse(
            question=clean_question,
            answer=rag_result.get("answer", "No answer generated."),
            sources=list(set(rag_result.get("sources", []))),
            context=context_items
        )

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering the question: {str(e)}"
        )


@app.post("/vector_store", response_model=IndexingResponse, tags=["Indexing"])
def trigger_indexing():
    """Trigger local document indexing for all PDFs in data/documents/."""
    try:
        logger.info("API trigger: Starting document indexing...")
        saved_indexes = index_all_documents()
        saved_paths_str = [str(path) for path in saved_indexes]

        return IndexingResponse(
            status="success" if saved_indexes else "no_files_found",
            indexed_files_count=len(saved_indexes),
            saved_paths=saved_paths_str
        )
    except Exception as e:
        logger.error(f"Error during indexing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during indexing: {str(e)}"
        )


# ------------------------------------------------------------------
# UI-Compatible Document Management Endpoints (New Feature Additions)
# ------------------------------------------------------------------

@app.get("/documents", response_model=List[DocumentItem], tags=["Documents"])
def list_documents():
    """List all stored documents and check if they have index files built."""
    try:
        docs_dir = Path(Config.DOCUMENTS_DIR)
        indexes_dir = Path(Config.INDEXES_DIR)
        
        docs_dir.mkdir(parents=True, exist_ok=True)
        indexes_dir.mkdir(parents=True, exist_ok=True)

        document_list = []
        for pdf_path in docs_dir.glob("*.pdf"):
            index_path = indexes_dir / f"{pdf_path.stem}_index.json"
            document_list.append(
                DocumentItem(
                    id=pdf_path.name,
                    filename=pdf_path.name,
                    size=pdf_path.stat().st_size,
                    indexed=index_path.exists()
                )
            )
        return document_list
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/upload", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Upload a new PDF to data/documents/ and index it immediately."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are currently supported by PageIndex."
        )

    try:
        docs_dir = Path(Config.DOCUMENTS_DIR)
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        destination = docs_dir / file.filename
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Index the newly uploaded document
        indexed_path = index_document(destination)

        return {
            "status": "success",
            "filename": file.filename,
            "indexed_path": str(indexed_path)
        }
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{filename}", tags=["Documents"])
def delete_document(filename: str):
    """Remove a PDF and its associated PageIndex JSON file."""
    try:
        pdf_path = Path(Config.DOCUMENTS_DIR) / filename
        index_path = Path(Config.INDEXES_DIR) / f"{Path(filename).stem}_index.json"

        deleted = False
        if pdf_path.exists():
            os.remove(pdf_path)
            deleted = True
        if index_path.exists():
            os.remove(index_path)

        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found.")

        return {"status": "success", "message": f"Deleted {filename}"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
