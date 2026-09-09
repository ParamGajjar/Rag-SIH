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

    FRONTEND_URL = os.getenv('FRONTEND_URL')
    @classmethod
    def ensure_directories(cls) -> None:
        """Create storage directories if they do not exist."""
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.INDEXES_DIR.mkdir(parents=True, exist_ok=True)

# Ensure folders exist when loaded
Config.ensure_directories()
