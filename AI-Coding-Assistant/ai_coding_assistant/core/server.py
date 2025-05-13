"""
Server module for the AI Coding Assistant.

This module implements the server that handles API requests and WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_coding_assistant.core.config import Config
from ai_coding_assistant.core.engine import Engine

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat messages."""

    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat messages."""

    message: str
    conversation_id: str
    tool_calls: List[Dict[str, Any]] = []


class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: str) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str) -> None:
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections.values():
            await connection.send_text(message)


class Server:
    """Server for the AI Coding Assistant."""

    def __init__(self, config: Config, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Initialize the server."""
        self.config = config
        self.host = host
        self.port = port
        self.app = FastAPI(title="AI Coding Assistant API")
        self.engine = Engine(config)
        self.connection_manager = ConnectionManager()

        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this to specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Set up routes
        self.setup_routes()

    def setup_routes(self) -> None:
        """Set up API routes."""
        @self.app.get("/")
        async def root() -> Dict[str, str]:
            return {"message": "AI Coding Assistant API"}

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest) -> ChatResponse:
            """Handle chat requests."""
            try:
                response = await self.engine.process_message(
                    request.message,
                    conversation_id=request.conversation_id,
                    context=request.context,
                )
                return response
            except Exception as e:
                logger.exception(f"Error processing chat request: {e}")
                raise

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
            """Handle WebSocket connections."""
            await self.connection_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        request_data = json.loads(data)
                        message = request_data.get("message", "")
                        conversation_id = request_data.get("conversation_id")
                        context = request_data.get("context", {})

                        # Process the message
                        response = await self.engine.process_message(
                            message, conversation_id=conversation_id, context=context
                        )

                        # Send the response
                        await websocket.send_text(json.dumps(response.dict()))
                    except json.JSONDecodeError:
                        await websocket.send_text(
                            json.dumps({"error": "Invalid JSON data"})
                        )
                    except Exception as e:
                        logger.exception(f"Error processing WebSocket message: {e}")
                        await websocket.send_text(
                            json.dumps({"error": f"Error processing message: {str(e)}"})
                        )
            except WebSocketDisconnect:
                self.connection_manager.disconnect(client_id)

    def start(self) -> None:
        """Start the server."""
        uvicorn.run(self.app, host=self.host, port=self.port)
