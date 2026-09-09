"""LLM Manager handling primary (OpenRouter) with fallback (Ollama) support."""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from app.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



class LLMManager:
    """Manages primary and fallback LLM execution cleanly."""

    def __init__(self):
        self.primary_llm = None
        self.fallback_llm = None

        # Setup Primary (OpenRouter) if API key is provided
        if Config.OPENROUTER_API_KEY.strip():
            self.primary_llm = ChatOpenAI(
                model=Config.OPENROUTER_MODEL,
                openai_api_key=Config.OPENROUTER_API_KEY,
                openai_api_base=Config.OPENROUTER_BASE_URL,
                temperature=0.1,
                timeout=45,
            )

       

    def ask(self, prompt: str) -> str:
        """Query primary LLM; fall back to local Ollama on any failure."""
        if self.primary_llm:
            try:
                logger.info(f"Querying Primary LLM (OpenRouter - {Config.OPENROUTER_MODEL})...")
                response = self.primary_llm.invoke(prompt)
                return str(response.content)
            except Exception as e:
                logger.warning(f"OpenRouter primary call failed: {e}. Falling back to Ollama...")

        if self.fallback_llm:
            try:
                logger.info(f"Querying Fallback LLM (Ollama - {Config.OLLAMA_MODEL})...")
                response = self.fallback_llm.invoke(prompt)
                print(response)
                print(response.content)
                return str(response.content)
            except Exception as e:
                logger.error(f"Ollama fallback also failed: {e}")
                return f"[Error]: Both Primary and Fallback LLMs failed. Details: {e}"

        return "[Error]: No valid LLM configuration found. Check your .env file."

# Singleton instance for simple module use
llm_manager = LLMManager()