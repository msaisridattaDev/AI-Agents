"""
Shell tools for the AI Coding Assistant.

This module provides tools for shell operations.
"""

import asyncio
import logging
import os
import shlex
import subprocess
from typing import Any, Dict, List

from ai_coding_assistant.tools.tool_registry import Tool

logger = logging.getLogger(__name__)


class ExecuteCommandTool(Tool):
    """Tool for executing shell commands."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "execute_command"

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return "Execute a shell command."

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters of the tool."""
        return {
            "command": {
                "type": "string",
                "description": "The command to execute",
            },
            "working_directory": {
                "type": "string",
                "description": "Optional working directory for the command",
            },
            "timeout": {
                "type": "integer",
                "description": "Optional timeout in seconds (default: 30)",
            }
        }

    @property
    def required(self) -> List[str]:
        """Get the required parameters of the tool."""
        return ["command"]

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        command = parameters["command"]
        working_directory = parameters.get("working_directory", os.getcwd())
        timeout = parameters.get("timeout", 30)
        
        try:
            # Validate command
            if self._is_dangerous_command(command):
                return {"error": f"Dangerous command not allowed: {command}"}
                
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                
                return {
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "exit_code": process.returncode,
                    "command": command,
                    "working_directory": working_directory,
                }
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                except Exception:
                    pass
                    
                return {
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command,
                    "working_directory": working_directory,
                }
                
        except Exception as e:
            logger.exception(f"Error executing command {command}: {e}")
            return {"error": f"Error executing command: {str(e)}"}

    def _is_dangerous_command(self, command: str) -> bool:
        """
        Check if a command is potentially dangerous.

        Args:
            command: The command to check

        Returns:
            True if the command is potentially dangerous, False otherwise
        """
        # Split the command into parts
        try:
            parts = shlex.split(command)
        except Exception:
            # If we can't parse the command, consider it dangerous
            return True
            
        if not parts:
            return False
            
        # Check for dangerous commands
        dangerous_commands = [
            "rm", "rmdir", "del", "format", "mkfs",
            "dd", "fdisk", "mkfs", "fsck",
            "chmod", "chown", "chgrp",
            ">", ">>", "2>", "2>>",
        ]
        
        # Check for dangerous flags
        dangerous_flags = [
            "-rf", "-fr", "-r -f", "-f -r",
            "--recursive", "--force",
            "/dev/", "/proc/", "/sys/",
            "sudo", "su", "passwd",
        ]
        
        # Check if the command or its flags are dangerous
        cmd = parts[0].lower()
        if cmd in dangerous_commands:
            return True
            
        for part in parts:
            for flag in dangerous_flags:
                if flag in part:
                    return True
                    
        # Check for shell redirections
        if ">" in command or ">>" in command:
            return True
            
        return False
