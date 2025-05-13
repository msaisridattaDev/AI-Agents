"""
Core engine for the AI Coding Assistant.

This module implements the main engine that coordinates all components.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ai_coding_assistant.agents.agent_manager import AgentManager
from ai_coding_assistant.context.context_manager import ContextManager
from ai_coding_assistant.core.config import Config
from ai_coding_assistant.memory.memory_manager import MemoryManager
from ai_coding_assistant.models.model_manager import ModelManager
from ai_coding_assistant.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class Engine:
    """
    Core engine for the AI Coding Assistant.
    
    This class coordinates all components and handles the main processing flow.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the engine with configuration."""
        self.config = config
        self.model_manager = ModelManager(config)
        self.context_manager = ContextManager(config)
        self.tool_registry = ToolRegistry(config)
        self.memory_manager = MemoryManager(config)
        self.agent_manager = AgentManager(config, self.model_manager, self.tool_registry)
        
        # Register built-in tools
        self._register_built_in_tools()
        
        logger.info("Engine initialized")

    def _register_built_in_tools(self) -> None:
        """Register built-in tools with the tool registry."""
        # Import tools here to avoid circular imports
        from ai_coding_assistant.tools.file_tools import (
            ReadFileTool,
            WriteFileTool,
            ListFilesTool,
        )
        from ai_coding_assistant.tools.shell_tools import ExecuteCommandTool
        from ai_coding_assistant.tools.search_tools import SearchCodeTool
        
        # Register tools
        self.tool_registry.register_tool(ReadFileTool())
        self.tool_registry.register_tool(WriteFileTool())
        self.tool_registry.register_tool(ListFilesTool())
        self.tool_registry.register_tool(ExecuteCommandTool())
        self.tool_registry.register_tool(SearchCodeTool())
        
        logger.info(f"Registered {len(self.tool_registry.get_tools())} built-in tools")

    async def process_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            message: The user's message
            conversation_id: Optional ID for the conversation
            context: Optional additional context
            
        Returns:
            A dictionary containing the response and any tool calls
        """
        # Generate or retrieve conversation ID
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        # Initialize context if not provided
        if context is None:
            context = {}
            
        try:
            # Store the message in memory
            self.memory_manager.add_message(conversation_id, "user", message)
            
            # Gather context
            context_items = await self.context_manager.gather_context(message, context)
            
            # Get available tools
            tools = self.tool_registry.get_tools()
            
            # Determine if we should use the agent or direct model call
            if self._should_use_agent(message, context):
                # Use agent for complex tasks
                logger.info(f"Using agent for message: {message[:50]}...")
                response, tool_calls = await self.agent_manager.process_task(
                    message, context_items, tools, conversation_id
                )
            else:
                # Use direct model call for simple queries
                logger.info(f"Using direct model call for message: {message[:50]}...")
                response, tool_calls = await self.model_manager.generate_response(
                    message, context_items, tools
                )
            
            # Store the response in memory
            self.memory_manager.add_message(conversation_id, "assistant", response)
            
            # Return the response
            return {
                "message": response,
                "conversation_id": conversation_id,
                "tool_calls": tool_calls
            }
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            raise

    def _should_use_agent(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determine if we should use the agent for this message.
        
        This is a simple heuristic that can be improved over time.
        """
        # Check if the message explicitly requests agent mode
        if "agent" in message.lower() or "autonomous" in message.lower():
            return True
            
        # Check if the message seems to be a complex task
        complex_indicators = [
            "create", "implement", "build", "refactor", "fix", "debug",
            "multiple", "files", "project", "generate", "test"
        ]
        
        # Count how many complex indicators are in the message
        indicator_count = sum(1 for indicator in complex_indicators if indicator in message.lower())
        
        # Use agent if there are multiple indicators of complexity
        return indicator_count >= 2
