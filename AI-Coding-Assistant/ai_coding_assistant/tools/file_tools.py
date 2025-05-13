"""
File tools for the AI Coding Assistant.

This module provides tools for file operations.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from ai_coding_assistant.tools.tool_registry import Tool

logger = logging.getLogger(__name__)


class ReadFileTool(Tool):
    """Tool for reading files."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "read_file"

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return "Read the content of a file."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        return {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read",
            }
        }

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return ["file_path"]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        file_path = parameters["file_path"]
        
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": f"File not found: {file_path}"}
                
            if not path.is_file():
                return {"error": f"Not a file: {file_path}"}
                
            # Check file size
            if path.stat().st_size > 1_000_000:  # 1MB limit
                return {"error": f"File too large: {file_path}"}
                
            # Check file extension
            if path.suffix.lower() in ['.exe', '.bin', '.dll', '.so', '.dylib', '.pyc']:
                return {"error": f"Binary file not supported: {file_path}"}
                
            # Read the file
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            return {
                "content": content,
                "file_path": file_path,
                "size": path.stat().st_size,
                "extension": path.suffix,
            }
            
        except Exception as e:
            logger.exception(f"Error reading file {file_path}: {e}")
            return {"error": f"Error reading file: {str(e)}"}


class WriteFileTool(Tool):
    """Tool for writing files."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "write_file"

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return "Write content to a file."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        return {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
            "append": {
                "type": "boolean",
                "description": "Whether to append to the file (default: false)",
            }
        }

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return ["file_path", "content"]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        file_path = parameters["file_path"]
        content = parameters["content"]
        append = parameters.get("append", False)
        
        try:
            path = Path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to the file
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
                
            return {
                "success": True,
                "file_path": file_path,
                "size": path.stat().st_size,
                "append": append,
            }
            
        except Exception as e:
            logger.exception(f"Error writing to file {file_path}: {e}")
            return {"error": f"Error writing to file: {str(e)}"}


class ListFilesTool(Tool):
    """Tool for listing files in a directory."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "list_files"

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return "List files in a directory."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        return {
            "directory": {
                "type": "string",
                "description": "Path to the directory to list files from",
            },
            "pattern": {
                "type": "string",
                "description": "Optional glob pattern to filter files",
            }
        }

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return ["directory"]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        directory = parameters["directory"]
        pattern = parameters.get("pattern", "*")
        
        try:
            path = Path(directory)
            if not path.exists():
                return {"error": f"Directory not found: {directory}"}
                
            if not path.is_dir():
                return {"error": f"Not a directory: {directory}"}
                
            # List files
            files = []
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix,
                    })
                    
            # List directories
            directories = []
            for dir_path in path.glob("*"):
                if dir_path.is_dir():
                    directories.append({
                        "name": dir_path.name,
                        "path": str(dir_path),
                    })
                    
            return {
                "files": files,
                "directories": directories,
                "directory": directory,
                "pattern": pattern,
            }
            
        except Exception as e:
            logger.exception(f"Error listing files in {directory}: {e}")
            return {"error": f"Error listing files: {str(e)}"}
