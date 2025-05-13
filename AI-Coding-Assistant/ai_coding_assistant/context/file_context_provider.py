"""
File context provider for the AI Coding Assistant.

This module provides context from files in the workspace.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_coding_assistant.context.context_manager import ContextProvider
from ai_coding_assistant.core.config import Config

logger = logging.getLogger(__name__)


class FileContextProvider(ContextProvider):
    """Context provider for files in the workspace."""

    def __init__(self, config: Config) -> None:
        """Initialize the file context provider with configuration."""
        self.config = config
        self._name = "file"
        self._priority = 90  # High priority

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
        Get context from files in the workspace.

        Args:
            query: The query to get context for
            options: Additional options for context retrieval

        Returns:
            A list of context items
        """
        context_items = []

        # Check if specific files are requested
        requested_files = options.get("files", [])
        current_file = options.get("current_file")
        
        # Add current file if specified
        if current_file:
            requested_files.append(current_file)
            
        # If no specific files are requested, return empty context
        if not requested_files:
            return []
            
        # Process each requested file
        for file_path in requested_files:
            try:
                # Read the file
                content = self._read_file(file_path)
                if content:
                    # Create a context item
                    context_item = {
                        "type": "file",
                        "source": file_path,
                        "content": content,
                        "relevance_score": 1.0 if file_path == current_file else 0.8,
                    }
                    context_items.append(context_item)
            except Exception as e:
                logger.exception(f"Error reading file {file_path}: {e}")

        return context_items

    def _read_file(self, file_path: str) -> Optional[str]:
        """
        Read a file and return its content.

        Args:
            file_path: Path to the file

        Returns:
            The file content or None if the file cannot be read
        """
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                logger.warning(f"File not found: {file_path}")
                return None
                
            # Check file size
            if path.stat().st_size > 1_000_000:  # 1MB limit
                logger.warning(f"File too large: {file_path}")
                return None
                
            # Check file extension
            if path.suffix.lower() in ['.exe', '.bin', '.dll', '.so', '.dylib', '.pyc']:
                logger.warning(f"Binary file not supported: {file_path}")
                return None
                
            # Read the file
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            logger.exception(f"Error reading file {file_path}: {e}")
            return None
