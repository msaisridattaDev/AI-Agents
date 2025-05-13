"""
Conversation context provider for the AI Coding Assistant.

This module provides context from the conversation history.
"""

import logging
from typing import Any, Dict, List

from ai_coding_assistant.context.context_manager import ContextProvider
from ai_coding_assistant.core.config import Config
from ai_coding_assistant.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ConversationContextProvider(ContextProvider):
    """Context provider for conversation history."""

    def __init__(self, config: Config) -> None:
        """Initialize the conversation context provider with configuration."""
        self.config = config
        self._name = "conversation"
        self._priority = 80  # High priority
        self.memory_manager = MemoryManager(config)

    @property
    def name(self) -> str:
        """Get the name of the context provider."""
        return self._name

    @property
    def priority(self) -> int:
        """Get the priority of the context provider."""
        return self._priority

    async def get_context(
        self, query: str, options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get context from conversation history.

        Args:
            query: The query to get context for
            options: Additional options for context retrieval

        Returns:
            A list of context items
        """
        context_items = []

        # Get conversation ID from options
        conversation_id = options.get("conversation_id")
        if not conversation_id:
            return []

        # Get conversation history
        try:
            # Get messages from memory
            messages = self.memory_manager.get_messages(conversation_id)
            
            # Skip if no messages
            if not messages:
                return []
                
            # Format conversation history
            conversation_text = ""
            for message in messages:
                role = message.get("role", "unknown")
                content = message.get("content", "")
                conversation_text += f"{role.capitalize()}: {content}\n\n"
                
            # Create a context item
            context_item = {
                "type": "conversation",
                "source": f"conversation:{conversation_id}",
                "content": conversation_text,
                "relevance_score": 0.9,  # High relevance for conversation history
            }
            context_items.append(context_item)
            
        except Exception as e:
            logger.exception(f"Error getting conversation history: {e}")

        return context_items
