import logging
from threading import Lock
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class ConversationMemoryManager:
    """Lightweight in-memory conversation turn manager"""
    
    def __init__(self, max_history_turns: int = 4):
        self.max_history_turns = max_history_turns
        self._history: Dict[str, List[Tuple[str, str]]] = {}
        self._lock = Lock()

    def add_turn(self, conversation_id: str, user_message: str, assistant_response: str):
        """Record user message and assistant answer in session history"""
        with self._lock:
            if conversation_id not in self._history:
                self._history[conversation_id] = []
            
            self._history[conversation_id].append((user_message, assistant_response))
            # Keep only recent N turns
            if len(self._history[conversation_id]) > self.max_history_turns:
                self._history[conversation_id] = self._history[conversation_id][-self.max_history_turns:]

    def get_history_formatted(self, conversation_id: str) -> str:
        """Format past turns into text for LLM context prompt"""
        with self._lock:
            turns = self._history.get(conversation_id, [])
            if not turns:
                return ""
            
            formatted_turns = []
            for user_msg, ai_msg in turns:
                formatted_turns.append(f"User: {user_msg}\nAssistant: {ai_msg}")
            return "\n\n".join(formatted_turns)

    def clear_history(self, conversation_id: str):
        """Clear history for a specific conversation session"""
        with self._lock:
            if conversation_id in self._history:
                del self._history[conversation_id]

# Singleton instance
chat_memory_manager = ConversationMemoryManager(max_history_turns=4)
