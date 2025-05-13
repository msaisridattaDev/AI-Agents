"""
Search tools for the AI Coding Assistant.

This module provides tools for searching code and documentation.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_coding_assistant.tools.tool_registry import Tool

logger = logging.getLogger(__name__)


class SearchCodeTool(Tool):
    """Tool for searching code in the workspace."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "search_code"

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return "Search for code in the workspace."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        return {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "directory": {
                "type": "string",
                "description": "Optional directory to search in",
            },
            "file_pattern": {
                "type": "string",
                "description": "Optional file pattern to search in (e.g., '*.py')",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether the search is case sensitive (default: false)",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 10)",
            }
        }

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return ["query"]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        query = parameters["query"]
        directory = parameters.get("directory", os.getcwd())
        file_pattern = parameters.get("file_pattern", "*")
        case_sensitive = parameters.get("case_sensitive", False)
        max_results = parameters.get("max_results", 10)
        
        try:
            # Validate directory
            path = Path(directory)
            if not path.exists():
                return {"error": f"Directory not found: {directory}"}
                
            if not path.is_dir():
                return {"error": f"Not a directory: {directory}"}
                
            # Compile regex pattern
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
            except re.error as e:
                return {"error": f"Invalid regex pattern: {str(e)}"}
                
            # Search for matches
            results = []
            for file_path in self._find_files(path, file_pattern):
                try:
                    matches = self._search_file(file_path, pattern)
                    if matches:
                        results.extend(matches)
                        if len(results) >= max_results:
                            break
                except Exception as e:
                    logger.warning(f"Error searching file {file_path}: {e}")
                    
            # Truncate results if necessary
            if len(results) > max_results:
                results = results[:max_results]
                
            return {
                "results": results,
                "query": query,
                "directory": directory,
                "file_pattern": file_pattern,
                "case_sensitive": case_sensitive,
                "total_results": len(results),
            }
            
        except Exception as e:
            logger.exception(f"Error searching code: {e}")
            return {"error": f"Error searching code: {str(e)}"}

    def _find_files(self, directory: Path, pattern: str) -> List[Path]:
        """
        Find files matching a pattern in a directory.

        Args:
            directory: Directory to search in
            pattern: File pattern to match

        Returns:
            List of matching file paths
        """
        # Define directories to ignore
        ignore_dirs = [
            ".git", "__pycache__", "node_modules", "venv", "env",
            ".vscode", ".idea", "dist", "build",
        ]
        
        # Define file extensions to ignore
        ignore_extensions = [
            ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
            ".mp3", ".mp4", ".avi", ".mov", ".mkv",
            ".zip", ".tar", ".gz", ".rar", ".7z",
        ]
        
        matching_files = []
        
        for root, dirs, files in os.walk(directory):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            # Check each file
            for file in files:
                # Skip ignored extensions
                if any(file.endswith(ext) for ext in ignore_extensions):
                    continue
                    
                # Check if file matches pattern
                file_path = Path(root) / file
                if file_path.match(pattern):
                    matching_files.append(file_path)
                    
        return matching_files

    def _search_file(self, file_path: Path, pattern: re.Pattern) -> List[Dict[str, Any]]:
        """
        Search for a pattern in a file.

        Args:
            file_path: Path to the file to search
            pattern: Regex pattern to search for

        Returns:
            List of matches
        """
        matches = []
        
        try:
            # Check file size
            if file_path.stat().st_size > 1_000_000:  # 1MB limit
                return []
                
            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                
            # Search for matches
            for i, line in enumerate(lines):
                for match in pattern.finditer(line):
                    # Get context (lines before and after)
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = lines[context_start:context_end]
                    
                    # Add match
                    matches.append({
                        "file": str(file_path),
                        "line": i + 1,
                        "column": match.start() + 1,
                        "match": match.group(0),
                        "context": "".join(context),
                    })
                    
            return matches
            
        except Exception as e:
            logger.warning(f"Error searching file {file_path}: {e}")
            return []
