"""Event emission endpoints for service-to-service communication"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# Router will be created with sio dependency
def create_emit_router(sio):
    """Create emit router with Socket.IO instance"""
    router = APIRouter(prefix="/emit", tags=["emit"])

    @router.post("/tree-progress")
    async def emit_tree_progress(data: dict):
        """Emit tree generation progress to all connected clients"""
        logger.info(f"Emitting tree progress: {data.get('document_id')}")
        await sio.emit('tree:progress', data)
        return {"status": "emitted", "event": "tree:progress"}

    @router.post("/tree-started")
    async def emit_tree_started(data: dict):
        """Emit tree generation started event"""
        logger.info(f"Emitting tree started: {data.get('document_id')}")
        await sio.emit('tree:started', data)
        return {"status": "emitted", "event": "tree:started"}

    @router.post("/tree-completed")
    async def emit_tree_completed(data: dict):
        """Emit tree generation completed event"""
        logger.info(f"Emitting tree completed: {data.get('document_id')}")
        await sio.emit('tree:completed', data)
        return {"status": "emitted", "event": "tree:completed"}

    @router.post("/tree-error")
    async def emit_tree_error(data: dict):
        """Emit tree generation error event"""
        logger.error(f"Emitting tree error: {data.get('document_id')}")
        await sio.emit('tree:error', data)
        return {"status": "emitted", "event": "tree:error"}

    @router.post("/document-update")
    async def emit_document_update(data: dict):
        """Emit document status update"""
        logger.info(f"Emitting document update: {data.get('document_id')}")
        await sio.emit('document:update', data)
        return {"status": "emitted", "event": "document:update"}

    @router.post("/query-progress")
    async def emit_query_progress(data: dict):
        """Emit query processing progress"""
        logger.info(f"Emitting query progress: {data.get('stage')}")
        await sio.emit('query:progress', data)
        return {"status": "emitted", "event": "query:progress"}

    return router
