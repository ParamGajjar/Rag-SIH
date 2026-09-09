"""LLM Manager handling primary (Groq) with OpenRouter / Ollama fallback support."""

import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LLMManager:
    """Manages primary (Groq) and fallback LLM execution cleanly."""

    def __init__(self):
        self.primary_llm = None
        self.fallback_llm = None

        # Setup Primary (Groq) if GROQ_API_KEY is provided
        if Config.GROQ_API_KEY and Config.GROQ_API_KEY.strip():
            try:
                logger.info(f"Initializing Primary Groq LLM with model: {Config.GROQ_MODEL}")
                self.primary_llm = ChatGroq(
                    model_name=Config.GROQ_MODEL,
                    groq_api_key=Config.GROQ_API_KEY,
                    temperature=0.1,
                    timeout=45,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGroq directly: {e}. Trying ChatOpenAI with Groq base URL...")
                self.primary_llm = ChatOpenAI(
                    model=Config.GROQ_MODEL,
                    openai_api_key=Config.GROQ_API_KEY,
                    openai_api_base=Config.GROQ_BASE_URL,
                    temperature=0.1,
                    timeout=45,
                )
        # Setup Fallback (OpenRouter) if OPENROUTER_API_KEY is provided
        elif Config.OPENROUTER_API_KEY and Config.OPENROUTER_API_KEY.strip():
            logger.info(f"Initializing Primary OpenRouter LLM with model: {Config.OPENROUTER_MODEL}")
            self.primary_llm = ChatOpenAI(
                model=Config.OPENROUTER_MODEL,
                openai_api_key=Config.OPENROUTER_API_KEY,
                openai_api_base=Config.OPENROUTER_BASE_URL,
                temperature=0.1,
                timeout=45,
            )

    def ask(self, prompt: str) -> str:
        """Query primary LLM; fall back to secondary on any failure."""
        if self.primary_llm:
            try:
                logger.info(f"Querying Primary LLM ({Config.GROQ_MODEL if Config.GROQ_API_KEY else Config.OPENROUTER_MODEL})...")
                response = self.primary_llm.invoke(prompt)
                return str(response.content)
            except Exception as e:
                logger.warning(f"Primary LLM call failed: {e}. Attempting fallback...")

        if self.fallback_llm:
            try:
                logger.info(f"Querying Fallback LLM (Ollama - {Config.OLLAMA_MODEL})...")
                response = self.fallback_llm.invoke(prompt)
                return str(response.content)
            except Exception as e:
                logger.error(f"Fallback LLM also failed: {e}")
                return f"[Error]: Both Primary and Fallback LLMs failed. Details: {e}"

        return "[Error]: No valid LLM configuration found. Set GROQ_API_KEY or OPENROUTER_API_KEY in your .env file."


# Singleton instance for simple module use
llm_manager = LLMManager()