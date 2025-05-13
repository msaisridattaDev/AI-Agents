"""
Repository context provider for the AI Coding Assistant.

This module provides context from the repository.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_coding_assistant.context.context_manager import ContextProvider
from ai_coding_assistant.core.config import Config

logger = logging.getLogger(__name__)


class RepositoryContextProvider(ContextProvider):
    """Context provider for repository information."""

    def __init__(self, config: Config) -> None:
        """Initialize the repository context provider with configuration."""
        self.config = config
        self._name = "repository"
        self._priority = 70  # Medium-high priority

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
        Get context from the repository.

        Args:
            query: The query to get context for
            options: Additional options for context retrieval

        Returns:
            A list of context items
        """
        context_items = []

        # Get repository path from options
        repo_path = options.get("repository_path", os.getcwd())
        
        try:
            # Get repository information
            repo_info = self._get_repository_info(repo_path)
            if repo_info:
                # Create a context item
                context_item = {
                    "type": "repository",
                    "source": "repository_info",
                    "content": repo_info,
                    "relevance_score": 0.7,
                }
                context_items.append(context_item)
                
            # Get project structure
            project_structure = self._get_project_structure(repo_path)
            if project_structure:
                # Create a context item
                context_item = {
                    "type": "repository",
                    "source": "project_structure",
                    "content": project_structure,
                    "relevance_score": 0.6,
                }
                context_items.append(context_item)
                
        except Exception as e:
            logger.exception(f"Error getting repository information: {e}")

        return context_items

    def _get_repository_info(self, repo_path: str) -> Optional[str]:
        """
        Get information about the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Repository information as a string
        """
        try:
            # Try to get Git repository information
            import git
            
            try:
                repo = git.Repo(repo_path)
                
                # Get repository information
                info = []
                info.append(f"Repository: {os.path.basename(repo.working_dir)}")
                
                try:
                    remote_url = repo.remotes.origin.url
                    info.append(f"Remote URL: {remote_url}")
                except (AttributeError, ValueError):
                    pass
                    
                try:
                    branch = repo.active_branch.name
                    info.append(f"Current Branch: {branch}")
                except (TypeError, ValueError):
                    pass
                
                return "\n".join(info)
                
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                # Not a Git repository or path doesn't exist
                return f"Directory: {os.path.basename(repo_path)}"
                
        except ImportError:
            logger.warning("GitPython not installed, cannot get Git repository information")
            return None
        except Exception as e:
            logger.exception(f"Error getting repository information: {e}")
            return None

    def _get_project_structure(self, repo_path: str) -> Optional[str]:
        """
        Get the project structure.

        Args:
            repo_path: Path to the repository

        Returns:
            Project structure as a string
        """
        try:
            path = Path(repo_path)
            if not path.exists() or not path.is_dir():
                return None
                
            # Get project structure
            structure = ["Project Structure:"]
            
            # Define files/directories to ignore
            ignore_patterns = [
                ".git", "__pycache__", "node_modules", "venv", "env",
                ".vscode", ".idea", "dist", "build", "*.pyc", "*.pyo",
                "*.pyd", "*.so", "*.dll", "*.exe", "*.bin"
            ]
            
            # Walk the directory tree
            for root, dirs, files in os.walk(path, topdown=True):
                # Filter directories
                dirs[:] = [d for d in dirs if not any(
                    d == p or (p.startswith("*") and d.endswith(p[1:]))
                    for p in ignore_patterns
                )]
                
                # Calculate relative path
                rel_path = os.path.relpath(root, path)
                if rel_path == ".":
                    level = 0
                else:
                    level = rel_path.count(os.sep) + 1
                    
                # Add directory to structure
                if level <= 3:  # Limit depth to avoid too much detail
                    indent = "  " * level
                    dir_name = os.path.basename(root)
                    if level > 0:
                        structure.append(f"{indent}- {dir_name}/")
                    
                    # Add files in directory
                    if level < 3:  # Only show files for top levels
                        for file in sorted(files):
                            if not any(
                                file == p or (p.startswith("*") and file.endswith(p[1:]))
                                for p in ignore_patterns
                            ):
                                structure.append(f"{indent}  - {file}")
            
            return "\n".join(structure)
            
        except Exception as e:
            logger.exception(f"Error getting project structure: {e}")
            return None
