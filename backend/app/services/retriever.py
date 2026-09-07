import logging
from typing import List, Dict, Any, Optional
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.embedding import EmbeddingManager

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Handles query-based retrieval from the vector store"""
    
    def __init__(self, vector_store: VectorStoreManager, embedding_manager: EmbeddingManager):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks for a given query"""
        logger.info(f"Retrieving documents for query: '{query}' (top_k={top_k})")
        
        # Initialize store if needed
        self.vector_store.initialize_store()
        
        # Generate query embedding
        query_embeddings = self.embedding_manager.generate_embeddings([query])
        if query_embeddings.size == 0:
            return []
            
        query_embedding = query_embeddings[0]
        
        try:
            results = self.vector_store.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            retrieved_docs = []
            if results and results.get('documents') and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                ids = results['ids'][0]
                
                for i, (doc_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                    similarity_score = 1.0 - float(distance)
                    if similarity_score >= score_threshold:
                        retrieved_docs.append({
                            'id': doc_id,
                            'content': document,
                            'metadata': metadata,
                            'similarity_score': similarity_score,
                            'distance': distance,
                            'rank': i + 1
                        })
            logger.info(f"Retrieved {len(retrieved_docs)} relevant documents after filtering.")
            return retrieved_docs
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []
