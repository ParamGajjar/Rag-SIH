import os
import uuid
import logging
import numpy as np
import chromadb
from typing import List, Any, Optional
from backend.app.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages document embeddings in a ChromaDB vector store"""
    
    def __init__(self, collection_name: str = "pdf_documents", persist_directory: Optional[str] = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.client = None
        self.collection = None

    def initialize_store(self):
        """Initialize ChromaDB client and collection on demand"""
        if self.client is None or self.collection is None:
            try:
                os.makedirs(self.persist_directory, exist_ok=True)
                logger.info(f"Initializing ChromaDB client at: {self.persist_directory}")
                self.client = chromadb.PersistentClient(path=self.persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "PDF document embeddings for RAG"}
                )
                logger.info(f"Vector store ready. Existing count: {self.collection.count()}")
            except Exception as e:
                logger.error(f"Error initializing vector store: {e}")
                raise

    def add_documents(self, documents: List[Any], embeddings: np.ndarray):
        """Add document chunks and their vector embeddings to ChromaDB"""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
            
        self.initialize_store()
        logger.info(f"Adding {len(documents)} documents to vector store...")
        
        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)
            
            metadata = dict(doc.metadata)
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadatas.append(metadata)
            
            documents_text.append(doc.page_content)
            embeddings_list.append(embedding.tolist())
            
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text
            )
            logger.info(f"Added {len(documents)} docs. Total in collection: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            raise
