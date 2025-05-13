"""
Configuration management for the AI Coding Assistant.

This module handles loading, validation, and access to configuration settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pydantic
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for the LLM provider."""

    provider: str = "anthropic"
    model: str = "claude-3-opus-20240229"
    api_key: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 4000
    })

    @validator("api_key", pre=True, always=True)
    def validate_api_key(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate API key, checking environment variables if not provided."""
        if v:
            return v

        provider = values.get("provider", "anthropic")
        env_var = f"{provider.upper()}_API_KEY"
        env_key = os.environ.get(env_var)
        
        if not env_key:
            logger.warning(f"No API key provided for {provider} and {env_var} not found in environment")
        
        return env_key


class ToolConfig(BaseModel):
    """Configuration for a specific tool."""

    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    """Configuration for security settings."""

    data_sharing: str = "minimal"
    audit_logging: bool = True
    pii_detection: bool = True
    sensitive_data_patterns: List[str] = Field(default_factory=lambda: [
        "password", "api_key", "secret", "token", "credential"
    ])


class UIConfig(BaseModel):
    """Configuration for the user interface."""

    theme: str = "system"
    code_highlighting: bool = True
    suggestions_delay: int = 300
    max_suggestions: int = 5


class MemoryConfig(BaseModel):
    """Configuration for memory systems."""

    conversation_limit: int = 50
    vector_db: Dict[str, Any] = Field(default_factory=lambda: {
        "type": "local",
        "path": "./data/vector_db"
    })


class PerformanceConfig(BaseModel):
    """Configuration for performance settings."""

    cache_ttl: int = 3600
    max_parallel_requests: int = 5
    timeout: int = 60


class Config(BaseModel):
    """Main configuration for the AI Coding Assistant."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: Dict[str, ToolConfig] = Field(default_factory=dict)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Config":
        """Load configuration from a file."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Configuration file {path} not found, using default configuration")
            return cls()

        try:
            with open(path, "r") as f:
                config_data = json.load(f)
            return cls.parse_obj(config_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file {path}: {e}")
            raise
        except pydantic.ValidationError as e:
            logger.error(f"Invalid configuration in {path}: {e}")
            raise

    def to_file(self, path: Union[str, Path]) -> None:
        """Save configuration to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.dict(), f, indent=2)

    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """Get configuration for a specific tool."""
        if tool_name not in self.tools:
            self.tools[tool_name] = ToolConfig()
        return self.tools[tool_name]
