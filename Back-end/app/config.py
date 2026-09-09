"""Configuration loader for environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    

    # Local Directory Paths
    DOCUMENTS_DIR: Path = BASE_DIR / os.getenv("DOCUMENTS_PATH", "data/documents")
    INDEXES_DIR: Path = BASE_DIR / os.getenv("PAGEINDEX_STORAGE_PATH", "data/indexes")

    # Groq LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # OpenRouter Settings (Alternative / Fallback)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Ollama Settings (Local Fallback)
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    FRONTEND_URL = os.getenv('FRONTEND_URL')
    @classmethod
    def ensure_directories(cls) -> None:
        """Create storage directories if they do not exist."""
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.INDEXES_DIR.mkdir(parents=True, exist_ok=True)

# Ensure folders exist when loaded
Config.ensure_directories()
