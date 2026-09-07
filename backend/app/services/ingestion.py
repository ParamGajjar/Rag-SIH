import logging
from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def process_all_pdfs(pdf_directory: str) -> List[Any]:
    """Process all PDF files in a directory recursively"""
    all_documents = []
    pdf_dir = Path(pdf_directory)
    
    if not pdf_dir.exists():
        logger.warning(f"PDF directory does not exist: {pdf_directory}")
        return []
    
    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files to process in {pdf_directory}")
    
    for pdf_file in pdf_files:
        logger.info(f"Processing PDF file: {pdf_file.name}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            
            for doc in documents:
                doc.metadata['source_file'] = pdf_file.name
                doc.metadata['file_type'] = 'pdf'
            
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} pages from {pdf_file.name}")
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_file.name}: {e}")
            
    logger.info(f"Total documents loaded: {len(all_documents)}")
    return all_documents


def split_documents(documents: List[Any], chunk_size: int = 400, chunk_overlap: int = 90) -> List[Any]:
    """Split documents into smaller chunks for RAG storage"""
    if not documents:
        logger.warning("No documents provided for splitting")
        return []
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
    return split_docs
