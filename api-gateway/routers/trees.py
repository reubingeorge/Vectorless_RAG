"""Tree generation and management endpoints"""
from fastapi import APIRouter, HTTPException, Depends
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trees", tags=["trees"])


@router.post("/generate/{doc_id}")
async def generate_tree(doc_id: int, registry: ServiceRegistry = Depends(get_service_registry)):
    """Generate PageIndex tree for document"""
    try:
        client = registry.get("trees")
        response = await client.post("/generate", json={"doc_id": doc_id})
        return response.json()
    except Exception as e:
        logger.error(f"Tree generation failed for doc {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tree generation failed: {str(e)}")


@router.get("/{tree_id}")
async def get_tree(tree_id: int, registry: ServiceRegistry = Depends(get_service_registry)):
    """Get tree by ID"""
    try:
        client = registry.get("storage")
        response = await client.get(f"/trees/{tree_id}")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Tree not found")


@router.get("/document/{doc_id}")
async def get_tree_by_document(doc_id: int, registry: ServiceRegistry = Depends(get_service_registry)):
    """Get tree for document"""
    try:
        client = registry.get("storage")
        response = await client.get(f"/trees/document/{doc_id}")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Tree not found for document")
