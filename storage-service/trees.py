from fastapi import APIRouter, HTTPException
import json

from models import Tree
from database import get_db_connection

router = APIRouter(prefix="/trees", tags=["trees"])


@router.post("")
async def create_tree(tree: Tree):
    """Create a new tree"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trees (doc_id, tree_data, num_pages, num_nodes, config)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        tree.doc_id,
        json.dumps(tree.tree_data),
        tree.num_pages,
        tree.num_nodes,
        json.dumps(tree.config) if tree.config else None
    ))

    tree_id = cursor.lastrowid

    # Update document with tree_id and mark as indexed
    cursor.execute(
        "UPDATE documents SET tree_id = ?, status = 'indexed', processed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (tree_id, tree.doc_id)
    )

    conn.commit()
    conn.close()

    return {"id": tree_id, "message": "Tree created successfully"}


@router.get("/{tree_id}")
async def get_tree(tree_id: int):
    """Get tree by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    result = cursor.execute('''
        SELECT id, doc_id, tree_data, created_at
        FROM trees
        WHERE id = ?
    ''', (tree_id,)).fetchone()

    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Tree not found")

    return {
        "id": result[0],
        "doc_id": result[1],
        "tree_data": json.loads(result[2]),
        "created_at": result[3]
    }


@router.get("/document/{doc_id}")
async def get_tree_by_document(doc_id: int):
    """Get tree by document ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    result = cursor.execute('''
        SELECT id, doc_id, tree_data, created_at
        FROM trees
        WHERE doc_id = ?
    ''', (doc_id,)).fetchone()

    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Tree not found for this document")

    return {
        "id": result[0],
        "doc_id": result[1],
        "tree_data": json.loads(result[2]),
        "created_at": result[3]
    }
