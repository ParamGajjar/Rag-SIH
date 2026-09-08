import os
import logging
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

# Disable HuggingFace Hub and transformers progress bars during backend execution
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
try:
    import transformers.utils.logging as tf_logging
    tf_logging.disable_progress_bar()
except Exception:
    pass

try:
    from huggingface_hub.utils import disable_progress_bars as hf_disable_progress_bars
    hf_disable_progress_bars()
except Exception:
    pass

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Handles document embedding generation using SentenceTransformer"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None

    def _load_model(self):
        """Lazy load the SentenceTransformer model"""
        if self.model is None:
            try:
                os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
                try:
                    import transformers.utils.logging as tf_logging
                    tf_logging.disable_progress_bar()
                except Exception:
                    pass

                try:
                    from huggingface_hub.utils import disable_progress_bars as hf_disable_progress_bars
                    hf_disable_progress_bars()
                except Exception:
                    pass

                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Embedding model loaded successfully. Dimension: {self.model.get_embedding_dimension()}")
            except Exception as e:
                logger.error(f"Error loading embedding model {self.model_name}: {e}")
                raise

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of text strings"""
        if not texts:
            return np.array([])
            
        self._load_model()
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(texts, show_progress_bar=False)
        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        return embeddings
