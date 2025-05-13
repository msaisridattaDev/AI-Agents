"""
Model manager for the AI Coding Assistant.

This module handles interactions with language models.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type

from ai_coding_assistant.core.config import Config
from ai_coding_assistant.models.anthropic_provider import AnthropicProvider
from ai_coding_assistant.models.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_prompt: str, options: Dict[str, Any]
    ) -> str:
        """Generate text from the model."""
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: List[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate text with tool calls."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text."""
        pass

    @abstractmethod
    def get_context_window(self) -> int:
        """Get the context window size for the model."""
        pass


class ModelManager:
    """Manager for language model interactions."""

    def __init__(self, config: Config) -> None:
        """Initialize the model manager with configuration."""
        self.config = config
        self.provider = self._create_provider()
        logger.info(f"Initialized model manager with provider: {config.llm.provider}")

    def _create_provider(self) -> ModelProvider:
        """Create the appropriate model provider based on configuration."""
        provider_map: Dict[str, Type[ModelProvider]] = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
        }

        provider_class = provider_map.get(self.config.llm.provider.lower())
        if provider_class is None:
            raise ValueError(f"Unsupported model provider: {self.config.llm.provider}")

        return provider_class(self.config.llm)

    async def generate_response(
        self,
        message: str,
        context_items: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate a response to a user message.

        Args:
            message: The user's message
            context_items: List of context items to include
            tools: Optional list of tools to make available

        Returns:
            A tuple of (response_text, tool_calls)
        """
        # Format the prompt with context
        prompt, system_prompt = self._format_prompt(message, context_items)

        # Generate response
        if tools:
            # Format tools for the model
            formatted_tools = self._format_tools(tools)
            
            # Generate with tools
            response, tool_calls = await self.provider.generate_with_tools(
                prompt, system_prompt, formatted_tools, self.config.llm.parameters
            )
        else:
            # Generate without tools
            response = await self.provider.generate_text(
                prompt, system_prompt, self.config.llm.parameters
            )
            tool_calls = []

        return response, tool_calls

    def _format_prompt(
        self, message: str, context_items: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Format the prompt with context items.

        Args:
            message: The user's message
            context_items: List of context items to include

        Returns:
            A tuple of (prompt, system_prompt)
        """
        # Create system prompt
        system_prompt = (
            "You are an AI coding assistant that helps with programming tasks. "
            "You have access to the user's codebase and can help with code understanding, "
            "generation, and editing. Be concise, helpful, and accurate."
        )

        # Format context items
        context_text = ""
        for item in context_items:
            item_type = item.get("type", "unknown")
            content = item.get("content", "")
            source = item.get("source", "")
            
            if item_type == "file":
                context_text += f"\nFile: {source}\n```\n{content}\n```\n"
            elif item_type == "symbol":
                context_text += f"\nSymbol: {source}\n```\n{content}\n```\n"
            elif item_type == "documentation":
                context_text += f"\nDocumentation: {source}\n{content}\n"
            else:
                context_text += f"\n{content}\n"

        # Combine context and message
        if context_text:
            prompt = f"Here is some context that might be helpful:\n{context_text}\n\nUser: {message}"
        else:
            prompt = f"User: {message}"

        return prompt, system_prompt

    def _format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format tools for the model provider.

        Args:
            tools: List of tools to format

        Returns:
            Formatted tools list
        """
        formatted_tools = []
        for tool in tools:
            formatted_tool = {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
            }
            formatted_tools.append(formatted_tool)
        return formatted_tools
