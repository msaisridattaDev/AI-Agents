"""
OpenAI model provider for the AI Coding Assistant.

This module implements the ModelProvider interface for OpenAI's models.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

import openai
from openai import OpenAI

from ai_coding_assistant.core.config import LLMConfig
from ai_coding_assistant.models.model_manager import ModelProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the OpenAI provider with configuration."""
        self.config = config
        self.model = config.model
        self.client = OpenAI(api_key=config.api_key)
        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    async def generate_text(
        self, prompt: str, system_prompt: str, options: Dict[str, Any]
    ) -> str:
        """
        Generate text from the OpenAI model.

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

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            # Extract the response text
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.exception(f"Error generating text with OpenAI: {e}")
            raise

    async def generate_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: List[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate text with tool calls from the OpenAI model.

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

            # Format tools for OpenAI
            formatted_tools = []
            for tool in tools:
                formatted_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": tool.get("parameters", {}),
                            "required": tool.get("required", []),
                        },
                    },
                }
                formatted_tools.append(formatted_tool)

            # Call the OpenAI API with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                tools=formatted_tools,
            )

            # Extract the response text and tool calls
            response_text = response.choices[0].message.content or ""
            tool_calls = []

            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    if tool_call.type == "function":
                        # Parse the function arguments
                        try:
                            parameters = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            parameters = {}

                        tool_calls.append({
                            "name": tool_call.function.name,
                            "parameters": parameters,
                        })

            return response_text, tool_calls

        except Exception as e:
            logger.exception(f"Error generating text with tools with OpenAI: {e}")
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
            # Use tiktoken for token counting
            import tiktoken
            
            # Get the encoding for the model
            if "gpt-4" in self.model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in self.model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")
                
            # Count tokens
            return len(encoding.encode(text))
            
        except ImportError:
            logger.warning("tiktoken not installed, using rough token estimate")
            # Fallback to a rough estimate
            return len(text) // 4
        except Exception as e:
            logger.exception(f"Error counting tokens with tiktoken: {e}")
            # Fallback to a rough estimate
            return len(text) // 4

    def get_context_window(self) -> int:
        """
        Get the context window size for the model.

        Returns:
            The context window size in tokens
        """
        # Context window sizes for OpenAI models
        context_windows = {
            "gpt-4-turbo": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-4-vision-preview": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
        }

        # Get the context window for the model, defaulting to 8192
        for model_prefix, window_size in context_windows.items():
            if self.model.startswith(model_prefix):
                return window_size

        # Default context window
        return 8192
