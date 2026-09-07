import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from backend.app.config import settings
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.embedding import EmbeddingManager

logger = logging.getLogger(__name__)

def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms for BM25 ranking"""
    return [w.lower() for w in re.findall(r'\b\w+\b', text)]


class RAGRetriever:
    """Handles query-based dense and hybrid retrieval from ChromaDB vector store"""
    
    def __init__(self, vector_store: VectorStoreManager, embedding_manager: EmbeddingManager):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks with optional metadata filtering, hybrid search, and score thresholding.
        """
        effective_top_k = top_k if top_k is not None else settings.DEFAULT_TOP_K
        effective_threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD

        logger.info(
            f"Executing retrieval for query: '{query}' "
            f"(doc_filter={document_ids}, top_k={effective_top_k}, threshold={effective_threshold})"
        )

        # 1. Ensure ChromaDB client and collection are initialized
        self.vector_store.initialize_store()
        if self.vector_store.collection.count() == 0:
            logger.info("Vector store is empty. Returning 0 results.")
            return []

        # 2. Build ChromaDB metadata filter
        where_filter = None
        if document_ids:
            # Filter empty strings or Nones
            valid_ids = [d for d in document_ids if d and isinstance(d, str)]
            if len(valid_ids) == 1:
                where_filter = {"document_id": valid_ids[0]}
            elif len(valid_ids) > 1:
                where_filter = {"document_id": {"$in": valid_ids}}

        # 3. Generate query embedding
        query_embeddings = self.embedding_manager.generate_embeddings([query])
        if query_embeddings.size == 0:
            return []
        query_embedding = query_embeddings[0]

        total_in_store = self.vector_store.collection.count()
        if total_in_store == 0:
            logger.info("Vector store is empty. Returning 0 results.")
            return []

        # 4. Perform candidate retrieval from ChromaDB
        candidate_count = min(total_in_store, max(effective_top_k * 4, 20))
        try:
            query_kwargs = {
                "query_embeddings": [query_embedding.tolist()],
                "n_results": candidate_count
            }
            if where_filter:
                query_kwargs["where"] = where_filter

            results = self.vector_store.collection.query(**query_kwargs)
        except Exception as e:
            logger.error(f"Error querying ChromaDB vector store: {e}")
            return []

        if not results or not results.get('documents') or not results['documents'][0]:
            logger.info("No candidates returned from vector store.")
            return []

        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        ids = results['ids'][0]

        # 5. Calculate dense vector similarity scores
        candidates = []
        for doc_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            # ChromaDB cosine space returns distance = 1 - cosine_similarity
            vector_score = max(0.0, min(1.0, float(1.0 - distance)))
            candidates.append({
                "chunk_id": metadata.get("chunk_id", doc_id),
                "document_id": metadata.get("document_id", "unknown"),
                "filename": metadata.get("filename", metadata.get("source", "unknown")),
                "page": int(metadata.get("page", 1)),
                "content": text,
                "vector_score": vector_score,
                "metadata": metadata
            })

        # 6. Apply Sparse BM25 boosting if enabled
        if settings.ENABLE_HYBRID_SEARCH and candidates:
            query_tokens = tokenize_text(query)
            corpus_tokens = [tokenize_text(c["content"]) for c in candidates]
            
            if query_tokens and any(corpus_tokens):
                bm25 = BM25Okapi(corpus_tokens)
                bm25_scores = bm25.get_scores(query_tokens)
                max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
                
                for c, bm_score in zip(candidates, bm25_scores):
                    norm_bm25 = float(bm_score / max_bm25) if max_bm25 > 0 else 0.0
                    # Boost score with BM25 keyword matches without penalizing vector score
                    fused_score = max(c["vector_score"], 0.75 * c["vector_score"] + 0.25 * norm_bm25)
                    c["similarity_score"] = float(round(fused_score, 4))
            else:
                for c in candidates:
                    c["similarity_score"] = float(round(c["vector_score"], 4))
        else:
            for c in candidates:
                c["similarity_score"] = float(round(c["vector_score"], 4))

        # 7. Sort by final similarity score descending
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        # 8. Filter by similarity threshold
        filtered_results = [
            c for c in candidates
            if c["similarity_score"] >= effective_threshold
        ]

        # 9. Return top_k results
        final_results = filtered_results[:effective_top_k]
        logger.info(f"Retrieved {len(final_results)} relevant chunks (after threshold={effective_threshold} filtering)")

        return [
            {
                "document_id": c["document_id"],
                "filename": c["filename"],
                "page": c["page"],
                "chunk_id": c["chunk_id"],
                "content": c["content"],
                "similarity_score": c["similarity_score"],
                "metadata": c["metadata"]
            }
            for c in final_results
        ]
