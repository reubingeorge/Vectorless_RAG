"""Settings and configuration endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/verify-key")
async def verify_api_key(
    request: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Verify OpenAI API key"""
    try:
        client = registry.get("settings")
        response = await client.post("/verify-key", json=request)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/save-key")
async def save_api_key(
    request: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Save OpenAI API key"""
    try:
        client = registry.get("settings")
        response = await client.post("/save-key", json=request)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/key-status")
async def get_key_status(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get API key status"""
    try:
        client = registry.get("settings")
        response = await client.get("/key-status")
        return response.json()
    except Exception as e:
        return {"status": "unchecked", "error": str(e)}


@router.get("/tree")
async def get_tree_settings(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get tree generation settings"""
    try:
        client = registry.get("settings")
        response = await client.get("/settings/tree")
        return response.json()
    except Exception as e:
        # Return defaults on error
        return {
            "toc_check_page_num": 20,
            "max_page_num_each_node": 10,
            "max_token_num_each_node": 20000
        }


@router.post("/tree")
async def update_tree_settings(
    settings: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update tree settings"""
    try:
        client = registry.get("settings")
        response = await client.post("/settings/tree", json=settings)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/query")
async def get_query_settings(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get query settings"""
    try:
        client = registry.get("settings")
        response = await client.get("/settings/query")
        return response.json()
    except Exception as e:
        return {"response_style": "balanced", "max_context_nodes": 5}


@router.post("/query")
async def update_query_settings(
    settings: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update query settings"""
    try:
        client = registry.get("settings")
        response = await client.post("/settings/query", json=settings)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model")
async def get_model_config(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get model configuration"""
    try:
        client = registry.get("settings")
        response = await client.get("/settings/model")
        return response.json()
    except Exception as e:
        return {"model": "gpt-4", "temperature": 0.7}


@router.post("/model")
async def update_model_config(
    config: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update model configuration"""
    try:
        client = registry.get("settings")
        response = await client.post("/settings/model", json=config)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ui")
async def get_ui_preferences(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get UI preferences"""
    try:
        client = registry.get("settings")
        response = await client.get("/settings/ui")
        return response.json()
    except Exception as e:
        return {"theme": "light", "fontSize": "medium"}


@router.post("/ui")
async def update_ui_preferences(
    prefs: Dict[str, Any],
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update UI preferences"""
    try:
        client = registry.get("settings")
        response = await client.post("/settings/ui", json=prefs)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Usage endpoint (different prefix)
usage_router = APIRouter(prefix="/api/usage", tags=["usage"])


@usage_router.get("/current-month")
async def get_usage(registry: ServiceRegistry = Depends(get_service_registry)):
    """Get usage statistics"""
    try:
        client = registry.get("settings")
        response = await client.get("/usage/current-month")
        return response.json()
    except Exception as e:
        return {"total_queries": 0, "total_cost": 0.0}
