"""
Memory manager for the AI Coding Assistant.

This module handles short-term and long-term memory.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_coding_assistant.core.config import Config

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manager for short-term and long-term memory."""

    def __init__(self, config: Config) -> None:
        """Initialize the memory manager with configuration."""
        self.config = config
        self.conversation_limit = config.memory.conversation_limit
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.data_dir = Path(config.memory.vector_db.get("path", "./data"))
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load conversations from disk
        self._load_conversations()
        
        logger.info("Initialized memory manager")

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (user or assistant)
            content: Content of the message
        """
        # Create conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        # Add message to conversation
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        self.conversations[conversation_id].append(message)
        
        # Limit conversation length
        if len(self.conversations[conversation_id]) > self.conversation_limit:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.conversation_limit:]
            
        # Save conversation to disk
        self._save_conversation(conversation_id)
        
        logger.debug(f"Added message to conversation {conversation_id}")

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of messages in the conversation
        """
        return self.conversations.get(conversation_id, [])

    def get_conversation_ids(self) -> List[str]:
        """
        Get all conversation IDs.

        Returns:
            List of conversation IDs
        """
        return list(self.conversations.keys())

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if the conversation was deleted, False otherwise
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            # Delete conversation file
            conversation_file = self.data_dir / f"conversation_{conversation_id}.json"
            if conversation_file.exists():
                conversation_file.unlink()
                
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        return False

    def _save_conversation(self, conversation_id: str) -> None:
        """
        Save a conversation to disk.

        Args:
            conversation_id: ID of the conversation to save
        """
        try:
            conversation_file = self.data_dir / f"conversation_{conversation_id}.json"
            with open(conversation_file, "w") as f:
                json.dump(self.conversations[conversation_id], f)
        except Exception as e:
            logger.exception(f"Error saving conversation {conversation_id}: {e}")

    def _load_conversations(self) -> None:
        """Load conversations from disk."""
        try:
            # Find conversation files
            for file in self.data_dir.glob("conversation_*.json"):
                try:
                    # Extract conversation ID from filename
                    conversation_id = file.stem.replace("conversation_", "")
                    
                    # Load conversation
                    with open(file, "r") as f:
                        self.conversations[conversation_id] = json.load(f)
                        
                    logger.debug(f"Loaded conversation {conversation_id}")
                except Exception as e:
                    logger.exception(f"Error loading conversation from {file}: {e}")
        except Exception as e:
            logger.exception(f"Error loading conversations: {e}")

    def add_to_long_term_memory(self, key: str, value: Any) -> None:
        """
        Add an item to long-term memory.

        Args:
            key: Key for the item
            value: Value to store
        """
        try:
            # Create memory file
            memory_file = self.data_dir / "long_term_memory.json"
            
            # Load existing memory
            if memory_file.exists():
                with open(memory_file, "r") as f:
                    memory = json.load(f)
            else:
                memory = {}
                
            # Add item to memory
            memory[key] = {
                "value": value,
                "timestamp": time.time(),
            }
            
            # Save memory
            with open(memory_file, "w") as f:
                json.dump(memory, f)
                
            logger.debug(f"Added item to long-term memory: {key}")
        except Exception as e:
            logger.exception(f"Error adding to long-term memory: {e}")

    def get_from_long_term_memory(self, key: str) -> Optional[Any]:
        """
        Get an item from long-term memory.

        Args:
            key: Key for the item

        Returns:
            The stored value or None if not found
        """
        try:
            # Check if memory file exists
            memory_file = self.data_dir / "long_term_memory.json"
            if not memory_file.exists():
                return None
                
            # Load memory
            with open(memory_file, "r") as f:
                memory = json.load(f)
                
            # Get item from memory
            if key in memory:
                return memory[key]["value"]
                
            return None
        except Exception as e:
            logger.exception(f"Error getting from long-term memory: {e}")
            return None
