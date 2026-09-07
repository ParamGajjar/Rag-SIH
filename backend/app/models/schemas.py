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
