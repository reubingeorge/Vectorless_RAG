"""Pydantic models for chat service"""
from pydantic import BaseModel
from typing import Optional

class ChatMessage(BaseModel):
    conversation_id: int
    message: str
    document_id: Optional[int] = None

class QueryStreamRequest(BaseModel):
    question: str
    document_id: int
    conversation_id: int
    use_cache: bool = True
    include_citations: bool = True
