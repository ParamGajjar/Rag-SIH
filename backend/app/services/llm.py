import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from backend.app.config import settings

logger = logging.getLogger(__name__)

class GroqLLM:
    """Handles interaction with Groq LLM API"""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or settings.GROQ_MODEL
        self.api_key = api_key or settings.GROQ_API_KEY
        self._llm = None

    def _get_llm(self) -> ChatGroq:
        """Lazy load ChatGroq instance"""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
            
        if self._llm is None:
            logger.info(f"Initializing ChatGroq with model: {self.model_name}")
            self._llm = ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.model_name,
                temperature=0.1,
                max_tokens=1024
            )
        return self._llm

    def generate_response(self, query: str, context: str) -> str:
        """Generate response using context and prompt template"""
        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful AI assistant specializing in Indian Standards and BIS compliance. Use the following context to answer the question accurately and concisely.

Context:
{context}

Question: {question}

Answer: Provide a clear and informative answer based on the context above. If the context doesn't contain enough information to answer the question, say so."""
        )
        
        formatted_prompt = prompt_template.format(context=context, question=query)
        
        try:
            llm = self._get_llm()
            messages = [HumanMessage(content=formatted_prompt)]
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating Groq response: {e}")
            raise RuntimeError(f"LLM Generation failed: {str(e)}") from e
