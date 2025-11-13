"""
Tree Service - PageIndex Tree Generation
Generates hierarchical tree structures from PDF documents
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import logging
import os
from io import BytesIO

from page_index import page_index_main

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tree Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8005")
SETTINGS_SERVICE_URL = os.getenv("SETTINGS_SERVICE_URL", "http://settings-service:8007")


class TreeGenerationRequest(BaseModel):
    doc_id: int
    config_override: Optional[Dict[str, Any]] = None


class TreeGenerationResponse(BaseModel):
    doc_id: int
    tree_id: int
    status: str
    num_pages: int
    num_nodes: int
    message: str


@app.get("/")
async def root():
    return {"service": "Tree Service", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "tree-service",
        "port": 8002,
        "version": "1.0.0"
    }


@app.post("/generate", response_model=TreeGenerationResponse)
async def generate_tree(request: TreeGenerationRequest):
    """
    Generate PageIndex tree structure for a document.

    Steps:
    1. Get document from storage service
    2. Get settings from settings service (tree generation config + API key)
    3. Run PageIndex algorithm
    4. Save tree to storage service
    5. Return results
    """
    doc_id = request.doc_id

    try:
        logger.info(f"Starting tree generation for document {doc_id}")

        # Emit tree started event
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-started", json={
                    "doc_id": doc_id,
                    "progress": 0,
                    "message": "Starting tree generation..."
                })
        except Exception as e:
            logger.warning(f"Failed to emit tree started event: {e}")

        # Step 1: Get document info from storage
        async with httpx.AsyncClient(timeout=30.0) as client:
            doc_response = await client.get(f"{STORAGE_SERVICE_URL}/documents/{doc_id}")
            if doc_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Document not found")
            doc_info = doc_response.json()

        logger.info(f"Document info: {doc_info['filename']}")

        # Step 2: Get PDF file from storage
        async with httpx.AsyncClient(timeout=60.0) as client:
            pdf_response = await client.get(f"{STORAGE_SERVICE_URL}/documents/{doc_id}/file")
            if pdf_response.status_code != 200:
                raise HTTPException(status_code=404, detail="PDF file not found")
            pdf_bytes = pdf_response.content

        pdf_stream = BytesIO(pdf_bytes)
        logger.info(f"Downloaded PDF: {len(pdf_bytes)} bytes")

        # Step 3: Get tree generation settings
        async with httpx.AsyncClient(timeout=30.0) as client:
            settings_response = await client.get(f"{SETTINGS_SERVICE_URL}/settings/tree")
            if settings_response.status_code == 200:
                tree_config = settings_response.json()
            else:
                # Use defaults
                tree_config = {
                    "model": "gpt-4o-2024-11-20",
                    "toc_check_page_num": 20,
                    "max_page_num_each_node": 10,
                    "max_token_num_each_node": 20000,
                    "if_add_node_id": True,
                    "if_add_node_summary": False,
                    "if_add_node_text": False,
                }

        # Override with request config if provided
        if request.config_override:
            tree_config.update(request.config_override)

        logger.info(f"Tree config: {tree_config}")

        # Step 4: Get API key from settings
        async with httpx.AsyncClient(timeout=30.0) as client:
            key_response = await client.get(f"{SETTINGS_SERVICE_URL}/get-key")
            if key_response.status_code != 200:
                raise HTTPException(status_code=500, detail="OpenAI API key not configured. Please add your API key in settings.")
            api_key = key_response.json()["key"]

        logger.info("Retrieved API key")

        # Emit progress: Starting PageIndex algorithm
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-progress", json={
                    "doc_id": doc_id,
                    "progress": 30,
                    "message": "Running PageIndex algorithm..."
                })
        except Exception as e:
            logger.warning(f"Failed to emit progress: {e}")

        # Create progress callback for detailed updates
        async def emit_progress(progress: int, message: str):
            """Emit progress updates to frontend via WebSocket"""
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post("http://chat-service:8004/emit/tree-progress", json={
                        "doc_id": doc_id,
                        "progress": progress,
                        "message": message
                    })
            except Exception as e:
                logger.warning(f"Failed to emit progress: {e}")

        # Step 5: Run PageIndex algorithm
        logger.info("Running PageIndex algorithm...")
        result = await page_index_main(pdf_stream, tree_config, api_key, progress_callback=emit_progress)

        logger.info(f"Tree generated: {result['num_nodes']} nodes from {result['num_pages']} pages")

        # Emit progress: Tree generated
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-progress", json={
                    "doc_id": doc_id,
                    "progress": 80,
                    "message": f"Tree generated with {result['num_nodes']} nodes",
                    "num_nodes": result['num_nodes'],
                    "num_pages": result['num_pages']
                })
        except Exception as e:
            logger.warning(f"Failed to emit progress: {e}")

        # Step 6: Save tree to storage
        async with httpx.AsyncClient(timeout=30.0) as client:
            save_response = await client.post(
                f"{STORAGE_SERVICE_URL}/trees",
                json={
                    "doc_id": doc_id,
                    "tree_data": result['tree'],
                    "num_pages": result['num_pages'],
                    "num_nodes": result['num_nodes'],
                    "config": tree_config
                }
            )
            if save_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to save tree")
            tree_record = save_response.json()

        logger.info(f"Tree saved with ID: {tree_record['id']}")

        # Emit progress: Saving
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-progress", json={
                    "doc_id": doc_id,
                    "progress": 95,
                    "message": "Finalizing..."
                })
        except Exception as e:
            logger.warning(f"Failed to emit progress: {e}")

        # Step 7: Update document status
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.patch(
                f"{STORAGE_SERVICE_URL}/documents/{doc_id}",
                json={"status": "indexed"}
            )

        # Emit completion event
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-completed", json={
                    "doc_id": doc_id,
                    "tree_id": tree_record['id'],
                    "progress": 100,
                    "message": f"Tree generation completed! {result['num_nodes']} nodes created",
                    "num_nodes": result['num_nodes'],
                    "num_pages": result['num_pages']
                })
        except Exception as e:
            logger.warning(f"Failed to emit completion event: {e}")

        return TreeGenerationResponse(
            doc_id=doc_id,
            tree_id=tree_record['id'],
            status="completed",
            num_pages=result['num_pages'],
            num_nodes=result['num_nodes'],
            message=f"Successfully generated tree with {result['num_nodes']} nodes"
        )

    except HTTPException as he:
        # Emit error event
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-error", json={
                    "doc_id": doc_id,
                    "message": str(he.detail),
                    "progress": 0
                })
        except:
            pass
        raise he
    except Exception as e:
        logger.error(f"Error generating tree: {str(e)}", exc_info=True)
        # Emit error event
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post("http://chat-service:8004/emit/tree-error", json={
                    "doc_id": doc_id,
                    "message": f"Tree generation failed: {str(e)}",
                    "progress": 0
                })
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Tree generation failed: {str(e)}")


@app.get("/trees/{tree_id}")
async def get_tree(tree_id: int):
    """Get a generated tree by ID (proxies to storage service)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{STORAGE_SERVICE_URL}/trees/{tree_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Tree not found")
            return response.json()
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trees/document/{doc_id}")
async def get_tree_by_document(doc_id: int):
    """Get tree for a specific document (proxies to storage service)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{STORAGE_SERVICE_URL}/trees/document/{doc_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Tree not found for this document")
            return response.json()
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
