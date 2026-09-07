from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str = Field("ok", description="Server health status")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message description")
    detail: Optional[str] = Field(None, description="Additional error context")

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    top_k: int = Field(5, ge=1, le=20, description="Number of document chunks to retrieve")

class DocumentReference(BaseModel):
    title: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class QueryResponse(BaseModel):
    answer: str
    references: List[DocumentReference]

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    page_count: int
    total_chunks: int
    file_hash: str
    is_duplicate: bool = False

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    stored_path: str
    upload_time: str
    page_count: int
    total_chunks: int
    file_size: int
    file_hash: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total_count: int

class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: str
