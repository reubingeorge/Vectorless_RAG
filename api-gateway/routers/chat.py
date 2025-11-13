"""Chat and WebSocket endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/info")
async def chat_info():
    """Get WebSocket connection information for real-time chat"""
    return {
        "websocket_url": "ws://chat-service:8004",
        "socket_path": "/socket.io",
        "protocol": "socket.io",
        "events": {
            "client_to_server": [
                "query - Send a query to the chat service",
                "message - Send a message"
            ],
            "server_to_client": [
                "connected - Connection established",
                "query:started - Query processing started",
                "query:answer - Answer received",
                "query:completed - Query processing completed",
                "query:error - Query error occurred",
                "tree:progress - Tree generation progress",
                "tree:started - Tree generation started",
                "tree:completed - Tree generation completed",
                "tree:error - Tree generation error",
                "document:update - Document status updated"
            ]
        },
        "example_query": {
            "question": "What is the main topic of this document?",
            "document_id": 1,
            "conversation_id": 1,
            "use_cache": True,
            "include_citations": True
        }
    }


@router.post("/emit/{event_type}")
async def emit_chat_event(
    event_type: str,
    data: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Emit event to chat service (for internal service communication)"""
    try:
        client = registry.get("chat")
        response = await client.post(
            f"/emit/{event_type}",
            json=data
        )
        return response.json()
    except Exception as e:
        logger.error(f"Failed to emit event {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to emit event: {str(e)}")
