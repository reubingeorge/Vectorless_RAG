from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from datetime import datetime
import os

from models import Document
from database import get_db_connection

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("")
async def create_document(doc: Document):
    """Create a new document record"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO documents (filename, file_path, size, page_count, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (doc.filename, doc.file_path, doc.size, doc.page_count, doc.status))

    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": doc_id, "message": "Document created successfully"}


@router.get("")
async def list_documents():
    """List all documents"""
    conn = get_db_connection()
    cursor = conn.cursor()

    results = cursor.execute('''
        SELECT id, filename, file_path, size, page_count, status, created_at, processed_at, tree_id
        FROM documents
        ORDER BY created_at DESC
    ''').fetchall()

    conn.close()

    documents = []
    for row in results:
        documents.append({
            "id": row[0],
            "filename": row[1],
            "file_path": row[2],
            "size": row[3],
            "page_count": row[4],
            "status": row[5],
            "created_at": row[6],
            "processed_at": row[7],
            "tree_id": row[8]
        })

    return {"documents": documents}


@router.get("/{doc_id}")
async def get_document(doc_id: int):
    """Get document by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    result = cursor.execute('''
        SELECT id, filename, file_path, size, page_count, status, created_at, processed_at, tree_id
        FROM documents
        WHERE id = ?
    ''', (doc_id,)).fetchone()

    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": result[0],
        "filename": result[1],
        "file_path": result[2],
        "size": result[3],
        "page_count": result[4],
        "status": result[5],
        "created_at": result[6],
        "processed_at": result[7],
        "tree_id": result[8]
    }


@router.patch("/{doc_id}")
async def update_document(doc_id: int, status: Optional[str] = None,
                          page_count: Optional[int] = None, tree_id: Optional[int] = None):
    """Update document status"""
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status)
        if status == "ready":
            updates.append("processed_at = ?")
            params.append(datetime.now())

    if page_count is not None:
        updates.append("page_count = ?")
        params.append(page_count)

    if tree_id is not None:
        updates.append("tree_id = ?")
        params.append(tree_id)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    params.append(doc_id)
    query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, params)
    conn.commit()
    conn.close()

    return {"message": "Document updated successfully"}


@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    """Delete document and associated files"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get file path
    result = cursor.execute(
        "SELECT file_path FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()

    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = result[0]

    # Delete from database
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    cursor.execute("DELETE FROM trees WHERE doc_id = ?", (doc_id,))
    conn.commit()
    conn.close()

    # Delete file
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": "Document deleted successfully"}


@router.get("/{doc_id}/file")
async def get_document_file(doc_id: int):
    """Serve document file"""
    conn = get_db_connection()
    cursor = conn.cursor()

    result = cursor.execute(
        "SELECT file_path, filename FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()

    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path, filename = result

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=filename)
