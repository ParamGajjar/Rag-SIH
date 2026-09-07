import os
import json
import logging
from threading import Lock
from typing import List, Optional, Dict, Any
from backend.app.config import settings

logger = logging.getLogger(__name__)

class DocumentRegistry:
    """Persistent JSON Document Metadata Registry"""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or settings.DOCUMENTS_META_FILE
        self._lock = Lock()
        self._ensure_file()

    def _ensure_file(self):
        """Ensure parent directory and JSON file exist"""
        with self._lock:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            if not os.path.exists(self.filepath):
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump({}, f)

    def _read_data(self) -> Dict[str, Dict[str, Any]]:
        """Internal helper to read document store"""
        try:
            if not os.path.exists(self.filepath):
                return {}
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading document registry file: {e}")
            return {}

    def _write_data(self, data: Dict[str, Dict[str, Any]]):
        """Internal helper to write document store"""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing to document registry: {e}")
            raise

    def save_document(self, metadata: Dict[str, Any]):
        """Save or update document metadata record"""
        with self._lock:
            data = self._read_data()
            doc_id = metadata["document_id"]
            data[doc_id] = metadata
            self._write_data(data)
            logger.info(f"Registered document {doc_id} ({metadata['filename']})")

    def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata by document ID"""
        with self._lock:
            data = self._read_data()
            return data.get(document_id)

    def get_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Search document registry for existing document matching SHA-256 hash"""
        with self._lock:
            data = self._read_data()
            for doc in data.values():
                if doc.get("file_hash") == file_hash:
                    return doc
            return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed document metadata records"""
        with self._lock:
            data = self._read_data()
            return list(data.values())

    def delete_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Remove document record by document ID"""
        with self._lock:
            data = self._read_data()
            if document_id in data:
                removed = data.pop(document_id)
                self._write_data(data)
                logger.info(f"Removed document {document_id} from registry")
                return removed
            return None

# Singleton instance
document_registry = DocumentRegistry()
