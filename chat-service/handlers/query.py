"""Query event handler with streaming support"""
import logging
import httpx
import asyncio
import json
from config import QUERY_SERVICE, STORAGE_SERVICE

logger = logging.getLogger(__name__)


async def handle_query(sio, sid, data):
    """
    Handle query requests with streaming responses
    data = {
        "question": "...",
        "document_id": 123,
        "conversation_id": 456,
        "use_cache": true,
        "include_citations": true
    }
    """
    logger.info(f"Query from {sid}: {data.get('question', '')[:50]}...")

    try:
        # Validate data
        if not data.get("question"):
            await sio.emit('error', {
                'message': 'Question is required'
            }, to=sid)
            return

        if not data.get("document_id"):
            await sio.emit('error', {
                'message': 'Document ID is required'
            }, to=sid)
            return

        conversation_id = data.get("conversation_id")
        if not conversation_id:
            await sio.emit('error', {
                'message': 'Conversation ID is required'
            }, to=sid)
            return

        # Emit query started
        await sio.emit('query:started', {
            'question': data["question"],
            'conversation_id': conversation_id
        }, to=sid)

        # Call query service
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{QUERY_SERVICE}/query",
                json={
                    "question": data["question"],
                    "document_id": data["document_id"],
                    "use_cache": data.get("use_cache", True),
                    "include_citations": data.get("include_citations", True)
                }
            )

            if response.status_code == 200:
                result = response.json()

                # Stream thinking process character by character
                if result.get("thinking"):
                    thinking_text = result.get("thinking", "")
                    for i in range(0, len(thinking_text), 3):  # Stream 3 chars at a time
                        chunk = thinking_text[i:i+3]
                        await sio.emit('query:thinking_stream', {
                            'chunk': chunk,
                            'conversation_id': conversation_id
                        }, to=sid)
                        await asyncio.sleep(0.01)  # 10ms delay between chunks

                # Emit node list after thinking completes
                if result.get("relevant_nodes"):
                    await sio.emit('query:nodes', {
                        'node_list': result.get("relevant_nodes", []),
                        'conversation_id': conversation_id
                    }, to=sid)
                    await asyncio.sleep(0.3)  # Brief pause before answer

                # Stream answer character by character
                answer_text = result["answer"]
                for i in range(0, len(answer_text), 3):  # Stream 3 chars at a time
                    chunk = answer_text[i:i+3]
                    await sio.emit('query:answer_stream', {
                        'chunk': chunk,
                        'conversation_id': conversation_id
                    }, to=sid)
                    await asyncio.sleep(0.01)  # 10ms delay between chunks

                # Emit completion with metadata
                await sio.emit('query:answer_complete', {
                    'question': result["question"],
                    'citations': result.get("citations", []),
                    'tokens_used': result["tokens_used"],
                    'cost': result["cost"],
                    'cached': result.get("cached", False),
                    'relevant_nodes': result.get("relevant_nodes", []),
                    'conversation_id': conversation_id
                }, to=sid)

                # Save message to storage
                try:
                    # Save user message
                    await client.post(
                        f"{STORAGE_SERVICE}/conversations/{conversation_id}/messages",
                        json={
                            "role": "user",
                            "content": data["question"],
                            "tokens": 0,  # Will be calculated in storage service
                            "cost": 0.0
                        }
                    )

                    # Save assistant message
                    await client.post(
                        f"{STORAGE_SERVICE}/conversations/{conversation_id}/messages",
                        json={
                            "role": "assistant",
                            "content": result["answer"],
                            "tokens": result["tokens_used"],
                            "cost": result["cost"],
                            "metadata": json.dumps({
                                "citations": result.get("citations", []),
                                "cached": result.get("cached", False),
                                "relevant_nodes": result.get("relevant_nodes", [])
                            })
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to save messages: {e}")

                # Emit completion
                await sio.emit('query:completed', {
                    'conversation_id': conversation_id,
                    'tokens_used': result["tokens_used"],
                    'cost': result["cost"]
                }, to=sid)

            else:
                error_detail = response.json().get("detail", "Query failed")
                await sio.emit('query:error', {
                    'message': error_detail,
                    'conversation_id': conversation_id
                }, to=sid)

    except Exception as e:
        logger.error(f"Query handling error: {e}")
        await sio.emit('query:error', {
            'message': str(e),
            'conversation_id': data.get("conversation_id")
        }, to=sid)
