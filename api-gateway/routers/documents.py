"""Document management endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Upload PDF document with retry logic"""
    try:
        client = registry.get("documents")
        if not client:
            raise HTTPException(status_code=503, detail="Document service unavailable")

        # Read file content
        content = await file.read()
        files = {"file": (file.filename, content, file.content_type)}

        # Make request with automatic retries
        response = await client.post("/upload", files=files)
        return response.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("")
async def list_documents(registry: ServiceRegistry = Depends(get_service_registry)):
    """List all documents"""
    try:
        client = registry.get("storage")
        response = await client.get("/documents")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}")
async def get_document(doc_id: int, registry: ServiceRegistry = Depends(get_service_registry)):
    """Get document details"""
    try:
        client = registry.get("storage")
        response = await client.get(f"/documents/{doc_id}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, registry: ServiceRegistry = Depends(get_service_registry)):
    """Delete document"""
    try:
        client = registry.get("storage")
        response = await client.delete(f"/documents/{doc_id}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
