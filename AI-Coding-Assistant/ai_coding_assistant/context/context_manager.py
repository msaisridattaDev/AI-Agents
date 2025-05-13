"""
Context manager for the AI Coding Assistant.

This module handles gathering and managing context for LLM queries.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai_coding_assistant.context.file_context_provider import FileContextProvider
from ai_coding_assistant.context.conversation_context_provider import ConversationContextProvider
from ai_coding_assistant.context.repository_context_provider import RepositoryContextProvider
from ai_coding_assistant.core.config import Config

logger = logging.getLogger(__name__)


class ContextProvider(ABC):
    """Abstract base class for context providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the context provider."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Get the priority of the context provider (higher is more important)."""
        pass

    @abstractmethod
    async def get_context(
        self, query: str, options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get context items for a query.

        Args:
            query: The query to get context for
            options: Additional options for context retrieval

        Returns:
            A list of context items
        """
        pass


class ContextManager:
    """Manager for context gathering and prioritization."""

    def __init__(self, config: Config) -> None:
        """Initialize the context manager with configuration."""
        self.config = config
        self.providers: List[ContextProvider] = []
        
        # Register built-in context providers
        self._register_built_in_providers()
        
        logger.info(f"Initialized context manager with {len(self.providers)} providers")

    def _register_built_in_providers(self) -> None:
        """Register built-in context providers."""
        # Register built-in providers
        self.register_provider(FileContextProvider(self.config))
        self.register_provider(ConversationContextProvider(self.config))
        self.register_provider(RepositoryContextProvider(self.config))

    def register_provider(self, provider: ContextProvider) -> None:
        """
        Register a context provider.

        Args:
            provider: The context provider to register
        """
        self.providers.append(provider)
        # Sort providers by priority (descending)
        self.providers.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"Registered context provider: {provider.name}")

    async def gather_context(
        self, query: str, options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Gather context from all providers for a query.

        Args:
            query: The query to gather context for
            options: Additional options for context gathering

        Returns:
            A list of context items
        """
        all_context_items: List[Dict[str, Any]] = []
        
        # Gather context from all providers
        for provider in self.providers:
            try:
                context_items = await provider.get_context(query, options)
                all_context_items.extend(context_items)
                logger.debug(f"Got {len(context_items)} context items from {provider.name}")
            except Exception as e:
                logger.exception(f"Error getting context from {provider.name}: {e}")
        
        # Prioritize and select context items
        selected_items = self._prioritize_context(all_context_items, query)
        
        return selected_items

    def _prioritize_context(
        self, context_items: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        Prioritize and select context items based on relevance.

        Args:
            context_items: All gathered context items
            query: The original query

        Returns:
            A prioritized list of context items
        """
        # Sort by relevance score if available
        context_items.sort(
            key=lambda item: item.get("relevance_score", 0), reverse=True
        )
        
        # TODO: Implement more sophisticated context selection
        # For now, just return all items
        return context_items
