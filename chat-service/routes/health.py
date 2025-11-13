"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"service": "Chat Service", "status": "running"}


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "chat-service",
        "port": 8004,
        "version": "1.0.0",
        "websocket": "socket.io enabled",
        "features": ["query_streaming", "message_persistence", "real_time_updates"]
    }
