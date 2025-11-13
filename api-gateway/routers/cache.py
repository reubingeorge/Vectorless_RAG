"""Cache management endpoints"""
from fastapi import APIRouter, HTTPException, Depends
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get cache statistics"""
    try:
        client = registry.get("cache")
        response = await client.get("/cache/stats")
        return response.json()
    except Exception as e:
        return {"total_keys": 0, "hits": 0, "misses": 0}


@router.post("/clear")
async def clear_cache(registry: ServiceRegistry = Depends(get_service_registry)):
    """Clear all cache"""
    try:
        client = registry.get("cache")
        response = await client.post("/cache/clear")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
