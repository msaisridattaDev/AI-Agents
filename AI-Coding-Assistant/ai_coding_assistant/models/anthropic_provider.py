"""
Anthropic model provider for the AI Coding Assistant.

This module implements the ModelProvider interface for Anthropic's Claude models.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

import anthropic

from ai_coding_assistant.core.config import LLMConfig
from ai_coding_assistant.models.model_manager import ModelProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the Anthropic provider with configuration."""
        self.config = config
        self.model = config.model
        self.client = anthropic.Anthropic(api_key=config.api_key)
        logger.info(f"Initialized Anthropic provider with model: {self.model}")

    async def generate_text(
        self, prompt: str, system_prompt: str, options: Dict[str, Any]
    ) -> str:
        """
        Generate text from the Claude model.

        Args:
            prompt: The user's prompt
            system_prompt: The system prompt
            options: Model parameters

        Returns:
            The generated text
        """
        try:
            # Extract parameters
            temperature = options.get("temperature", 0.7)
            max_tokens = options.get("max_tokens", 4000)
            top_p = options.get("top_p", 0.9)

            # Call the Anthropic API
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            # Extract the response text
            return response.content[0].text

        except Exception as e:
            logger.exception(f"Error generating text with Anthropic: {e}")
            raise

    async def generate_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: List[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate text with tool calls from the Claude model.

        Args:
            prompt: The user's prompt
            system_prompt: The system prompt
            tools: List of tools to make available
            options: Model parameters

        Returns:
            A tuple of (response_text, tool_calls)
        """
        try:
            # Extract parameters
            temperature = options.get("temperature", 0.7)
            max_tokens = options.get("max_tokens", 4000)
            top_p = options.get("top_p", 0.9)

            # Format tools for Anthropic
            formatted_tools = []
            for tool in tools:
                formatted_tool = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "input_schema": {"type": "object", "properties": tool.get("parameters", {})},
                }
                formatted_tools.append(formatted_tool)

            # Call the Anthropic API with tools
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                tools=formatted_tools,
            )

            # Extract the response text and tool calls
            response_text = ""
            tool_calls = []

            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
                elif content_block.type == "tool_use":
                    tool_call = {
                        "name": content_block.name,
                        "parameters": content_block.input,
                    }
                    tool_calls.append(tool_call)

            return response_text, tool_calls

        except Exception as e:
            logger.exception(f"Error generating text with tools with Anthropic: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the text.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens
        """
        try:
            return self.client.count_tokens(text)
        except Exception as e:
            logger.exception(f"Error counting tokens with Anthropic: {e}")
            # Fallback to a rough estimate
            return len(text) // 4

    def get_context_window(self) -> int:
        """
        Get the context window size for the model.

        Returns:
            The context window size in tokens
        """
        # Context window sizes for Claude models
        context_windows = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 100000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
        }

        # Get the context window for the model, defaulting to 100000
        for model_prefix, window_size in context_windows.items():
            if self.model.startswith(model_prefix):
                return window_size

        # Default context window
        return 100000
