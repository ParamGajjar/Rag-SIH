import logging
from fastapi import APIRouter, status, HTTPException

from backend.app.models.schemas import (
    RetrieveRequest,
    RetrieveResponse,
    ChunkSearchResult
)
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.embedding import EmbeddingManager
from backend.app.services.retriever import RAGRetriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Retrieval"])

# Lazy singletons
embedding_manager = EmbeddingManager()
vectorstore_manager = VectorStoreManager()
retriever_service = RAGRetriever(vectorstore_manager, embedding_manager)


@router.post("/retrieve", response_model=RetrieveResponse, status_code=status.HTTP_200_OK)
def retrieve_chunks(request: RetrieveRequest):
    """
    Retrieve relevant document chunks based on semantic similarity and optional document filtering.
    """
    try:
        results = retriever_service.retrieve(
            query=request.query,
            document_ids=request.document_ids,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        chunk_results = [ChunkSearchResult(**r) for r in results]
        return RetrieveResponse(
            query=request.query,
            total_found=len(chunk_results),
            results=chunk_results
        )
    except Exception as e:
        logger.error(f"Error executing retrieval request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}"
        )
