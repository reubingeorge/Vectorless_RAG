from fastapi import APIRouter

from database import get_db_connection

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats():
    """Get storage statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    doc_count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    tree_count = cursor.execute("SELECT COUNT(*) FROM trees").fetchone()[0]
    conv_count = cursor.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    msg_count = cursor.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    total_size = cursor.execute("SELECT SUM(size) FROM documents").fetchone()[0] or 0

    conn.close()

    return {
        "documents": doc_count,
        "trees": tree_count,
        "conversations": conv_count,
        "messages": msg_count,
        "total_storage_bytes": total_size
    }
