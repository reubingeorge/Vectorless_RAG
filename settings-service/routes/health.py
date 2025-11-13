"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"service": "Settings Service", "status": "running"}


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "settings-service",
        "port": 8007,
        "version": "1.0.0"
    }
