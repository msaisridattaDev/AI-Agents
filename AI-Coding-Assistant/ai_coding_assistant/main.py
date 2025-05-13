#!/usr/bin/env python3
"""
Main entry point for the AI Coding Assistant.

This module initializes and runs the AI Coding Assistant server.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_coding_assistant.core.config import Config
from ai_coding_assistant.core.server import Server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI Coding Assistant")
    parser.add_argument(
        "--config", type=str, default="config.json", help="Path to configuration file"
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def main() -> None:
    """Initialize and run the AI Coding Assistant."""
    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    args = parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration file {config_path} not found, using default configuration")
            config = Config()
        else:
            config = Config.from_file(config_path)

        # Initialize server
        server = Server(config, host=args.host, port=args.port)

        # Start server
        logger.info(f"Starting AI Coding Assistant server on {args.host}:{args.port}")
        server.start()

    except Exception as e:
        logger.exception(f"Error starting AI Coding Assistant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
