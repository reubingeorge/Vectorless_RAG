"""Query processing endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from dependencies import get_service_registry, ServiceRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["queries"])


class QueryRequest(BaseModel):
    question: str
    document_id: int
    use_cache: bool = True
    include_citations: bool = True


@router.post("/query")
async def query_document(
    request: QueryRequest,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Query a document using PageIndex two-stage retrieval
    Stage 1: Tree search to find relevant nodes
    Stage 2: Answer generation with citations
    """
    try:
        client = registry.get("queries")
        response = await client.post(
            "/query",
            json=request.model_dump()
        )
        return response.json()
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
