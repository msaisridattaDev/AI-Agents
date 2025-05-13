"""
Tool registry for the AI Coding Assistant.

This module manages the available tools and their execution.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from ai_coding_assistant.core.config import Config

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the tool."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        pass

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return []

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        pass


class ToolRegistry:
    """Registry for tools."""

    def __init__(self, config: Config) -> None:
        """Initialize the tool registry with configuration."""
        self.config = config
        self.tools: Dict[str, Tool] = {}
        logger.info("Initialized tool registry")

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: The tool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Name of the tool

        Returns:
            The tool or None if not found
        """
        return self.tools.get(name)

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools.

        Returns:
            List of tool definitions
        """
        tool_defs = []
        for tool in self.tools.values():
            # Check if tool is enabled in config
            tool_config = self.config.get_tool_config(tool.name)
            if not tool_config.enabled:
                continue
                
            # Add tool definition
            tool_def = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "required": tool.required,
            }
            tool_defs.append(tool_def)
            
        return tool_defs

    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            name: Name of the tool to execute
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If the tool is not found or disabled
        """
        # Get the tool
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
            
        # Check if tool is enabled
        tool_config = self.config.get_tool_config(name)
        if not tool_config.enabled:
            raise ValueError(f"Tool is disabled: {name}")
            
        # Validate parameters
        self._validate_parameters(tool, parameters)
            
        # Execute the tool
        try:
            logger.info(f"Executing tool: {name}")
            result = await tool.execute(parameters)
            return result
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            raise

    def _validate_parameters(self, tool: Tool, parameters: Dict[str, Any]) -> None:
        """
        Validate parameters for a tool.

        Args:
            tool: The tool to validate parameters for
            parameters: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        # Check required parameters
        for param in tool.required:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")
                
        # Check parameter types (basic validation)
        for param_name, param_value in parameters.items():
            if param_name not in tool.parameters:
                raise ValueError(f"Unknown parameter: {param_name}")
                
            # TODO: Add more sophisticated type checking
