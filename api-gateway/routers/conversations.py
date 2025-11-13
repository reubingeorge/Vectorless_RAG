"""Conversation management endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(registry: ServiceRegistry = Depends(get_service_registry)):
    """List all conversations"""
    try:
        client = registry.get("storage")
        response = await client.get("/conversations")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        return []


@router.get("/{conv_id}")
async def get_conversation(conv_id: str, registry: ServiceRegistry = Depends(get_service_registry)):
    """Get conversation with messages"""
    try:
        client = registry.get("storage")
        response = await client.get(f"/conversations/{conv_id}")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("")
async def create_conversation(
    conversation: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Create new conversation"""
    try:
        client = registry.get("storage")
        response = await client.post("/conversations", json=conversation)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str, registry: ServiceRegistry = Depends(get_service_registry)):
    """Delete conversation"""
    try:
        client = registry.get("storage")
        response = await client.delete(f"/conversations/{conv_id}")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
