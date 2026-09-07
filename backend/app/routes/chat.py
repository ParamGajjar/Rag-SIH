import uuid
import logging
from typing import List
from fastapi import APIRouter, status, HTTPException

from backend.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SourceReference
)
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.embedding import EmbeddingManager
from backend.app.services.retriever import RAGRetriever
from backend.app.services.llm import GroqLLM
from backend.app.services.chat_memory import chat_memory_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])

# Lazy singletons
embedding_manager = EmbeddingManager()
vectorstore_manager = VectorStoreManager()
retriever_service = RAGRetriever(vectorstore_manager, embedding_manager)
groq_llm = GroqLLM()

NO_CONTEXT_FALLBACK_ANSWER = "Based on the provided documents, I could not find information to answer your question."


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_endpoint(request: ChatRequest):
    """
    Grounded Chat API endpoint executing vector retrieval, anti-hallucination checks, and Groq LLM inference.
    """
    # 1. Validate empty question
    user_query = request.message.strip() if request.message else ""
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    # 2. Manage conversation_id session
    session_id = request.conversation_id if request.conversation_id else f"conv_{uuid.uuid4().hex[:12]}"

    # 3. Retrieve relevant chunks
    try:
        retrieved_chunks = retriever_service.retrieve(
            query=user_query,
            document_ids=request.document_ids
        )
    except Exception as e:
        logger.error(f"Error during retrieval for chat: {e}")
        retrieved_chunks = []

    # 4. If no relevant chunks meet score threshold -> Return grounded fallback with ZERO LLM calls
    if not retrieved_chunks:
        logger.info(f"No relevant chunks found for query '{user_query}'. Returning grounded fallback.")
        return ChatResponse(
            answer=NO_CONTEXT_FALLBACK_ANSWER,
            sources=[],
            conversation_id=session_id
        )

    # 5. Format authentic sources
    sources: List[SourceReference] = [
        SourceReference(
            document=chunk["filename"],
            page=chunk["page"],
            content=chunk["content"],
            score=chunk["similarity_score"]
        )
        for chunk in retrieved_chunks
    ]

    # 6. Build prompt context string
    formatted_context_items = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        formatted_context_items.append(
            f"[Source {idx}: Document '{chunk['filename']}', Page {chunk['page']}]\n{chunk['content']}"
        )
    context_text = "\n\n".join(formatted_context_items)

    # 7. Get conversation history
    history_text = chat_memory_manager.get_history_formatted(session_id)

    # 8. Generate response via Groq LLM
    try:
        llm_answer = groq_llm.generate_grounded_response(
            query=user_query,
            context=context_text,
            conversation_history=history_text
        )
    except ValueError as ve:
        logger.error(f"Groq API key configuration error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Groq API key is not configured."
        )
    except RuntimeError as re:
        logger.error(f"Groq LLM service error: {re}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Groq LLM service failed: {str(re)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error calling Groq LLM: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation failed: {str(e)}"
        )

    # 9. Update conversation memory
    chat_memory_manager.add_turn(session_id, user_query, llm_answer)

    return ChatResponse(
        answer=llm_answer,
        sources=sources,
        conversation_id=session_id
    )
