"""Health check and statistics endpoints"""
from fastapi import APIRouter, Depends
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health(registry: ServiceRegistry = Depends(get_service_registry)):
    """Aggregated health check for all services"""
    health_status = await registry.health_check_all()

    # Determine overall status
    all_healthy = all(
        s.get("status") == "healthy"
        for s in health_status.values()
    )

    any_degraded = any(
        s.get("status") in ["timeout", "error"]
        for s in health_status.values()
    )

    any_down = any(
        s.get("status") == "unreachable"
        for s in health_status.values()
    )

    if all_healthy:
        overall_status = "healthy"
    elif any_down:
        overall_status = "critical"
    elif any_degraded:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "gateway": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "services": health_status,
        "summary": {
            "total": len(health_status),
            "healthy": sum(1 for s in health_status.values() if s.get("status") == "healthy"),
            "unhealthy": sum(1 for s in health_status.values() if s.get("status") != "healthy")
        }
    }


@router.get("/api/stats")
async def get_stats(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get aggregated statistics from all services"""
    stats = {}

    try:
        storage_client = registry.get("storage")
        storage_response = await storage_client.get("/stats")
        stats["storage"] = storage_response.json()
    except Exception as e:
        logger.error(f"Failed to get storage stats: {str(e)}")
        stats["storage"] = {"error": str(e)}

    try:
        cache_client = registry.get("cache")
        cache_response = await cache_client.get("/cache/stats")
        stats["cache"] = cache_response.json()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        stats["cache"] = {"error": str(e)}

    try:
        settings_client = registry.get("settings")
        usage_response = await settings_client.get("/usage/current-month")
        stats["usage"] = usage_response.json()
    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        stats["usage"] = {"error": str(e)}

    return stats
