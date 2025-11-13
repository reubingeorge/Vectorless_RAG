from fastapi import APIRouter, HTTPException
from datetime import datetime
import time

from models import Message, ConversationCreate
from database import get_db_connection

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("")
async def create_conversation(conv: ConversationCreate):
    """Create a new conversation"""
    # Auto-generate conversation ID
    conv_id = str(int(time.time() * 1000))  # Timestamp-based ID

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO conversations (id, title, doc_id)
        VALUES (?, ?, ?)
    ''', (conv_id, conv.title, conv.doc_id))

    conn.commit()

    # Get the created conversation
    result = cursor.execute('''
        SELECT id, title, doc_id, created_at, updated_at
        FROM conversations
        WHERE id = ?
    ''', (conv_id,)).fetchone()

    conn.close()

    return {
        "id": int(result[0]),
        "title": result[1],
        "doc_id": result[2],
        "created_at": result[3],
        "updated_at": result[4]
    }


@router.get("")
async def list_conversations():
    """List all conversations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    results = cursor.execute('''
        SELECT id, title, doc_id, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
    ''').fetchall()

    conn.close()

    conversations = []
    for row in results:
        conversations.append({
            "id": row[0],
            "title": row[1],
            "doc_id": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        })

    return {"conversations": conversations}


@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    """Get conversation with messages"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get conversation
    conv = cursor.execute('''
        SELECT id, title, doc_id, created_at, updated_at
        FROM conversations
        WHERE id = ?
    ''', (conv_id,)).fetchone()

    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    messages = cursor.execute('''
        SELECT id, role, content, tokens, cost, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conv_id,)).fetchall()

    conn.close()

    return {
        "id": conv[0],
        "title": conv[1],
        "doc_id": conv[2],
        "created_at": conv[3],
        "updated_at": conv[4],
        "messages": [
            {
                "id": msg[0],
                "role": msg[1],
                "content": msg[2],
                "tokens": msg[3],
                "cost": msg[4],
                "created_at": msg[5]
            }
            for msg in messages
        ]
    }


@router.post("/{conv_id}/messages")
async def add_message(conv_id: str, msg: Message):
    """Add a message to conversation"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add message
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content, tokens, cost)
        VALUES (?, ?, ?, ?, ?)
    ''', (conv_id, msg.role, msg.content, msg.tokens, msg.cost))

    msg_id = cursor.lastrowid

    # Update conversation updated_at
    cursor.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (datetime.now(), conv_id)
    )

    conn.commit()
    conn.close()

    return {"id": msg_id, "message": "Message added successfully"}


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete conversation and messages"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))

    conn.commit()
    conn.close()

    return {"message": "Conversation deleted successfully"}
