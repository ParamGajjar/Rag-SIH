"""
Rag-SIH Main Ingestion and Retrieval CLI Script.
Refactored to import from backend services without automatic side-effects on import.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root directory to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.services.ingestion import process_all_pdfs, split_documents
from backend.app.services.embedding import EmbeddingManager
from backend.app.services.vectorstore import VectorStoreManager
from backend.app.services.retriever import RAGRetriever
from backend.app.services.llm import GroqLLM

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rag_main")


def run_pipeline(pdf_directory: str = "../data", query: str = None):
    """Run full RAG ingestion and retrieval workflow on demand"""
    logger.info("Starting RAG ingestion pipeline...")
    
    # 1. Load PDFs
    all_documents = process_all_pdfs(pdf_directory)
    if not all_documents:
        logger.warning("No documents loaded. Ingestion cancelled.")
        return
        
    # 2. Split into chunks
    chunks = split_documents(all_documents, chunk_size=400, chunk_overlap=90)
    
    # 3. Generate embeddings
    embedding_manager = EmbeddingManager()
    texts = [doc.page_content for doc in chunks]
    embeddings = embedding_manager.generate_embeddings(texts)
    
    # 4. Add to Vector Store
    vectorstore = VectorStoreManager()
    vectorstore.add_documents(chunks, embeddings)
    
    # 5. Retrieve & LLM response if query provided
    if query:
        retriever = RAGRetriever(vectorstore, embedding_manager)
        retrieved = retriever.retrieve(query=query, top_k=5)
        
        context = "\n\n".join([doc['content'] for doc in retrieved])
        
        try:
            llm = GroqLLM()
            response = llm.generate_response(query=query, context=context)
            logger.info(f"Generated Response:\n{response}")
        except Exception as e:
            logger.error(f"Could not generate LLM response: {e}")


if __name__ == "__main__":
    # Standard CLI execution when run directly
    sample_query = "What standard applies to occupational safety and health audit?"
    run_pipeline(pdf_directory="../data", query=sample_query)
