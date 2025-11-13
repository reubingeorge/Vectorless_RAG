from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Document(BaseModel):
    id: Optional[int] = None
    filename: str
    file_path: str
    size: int
    page_count: Optional[int] = None
    status: str = "uploaded"  # uploaded, processing, ready, failed
    created_at: Optional[str] = None
    processed_at: Optional[str] = None
    tree_id: Optional[int] = None


class Tree(BaseModel):
    id: Optional[int] = None
    doc_id: int
    tree_data: List[Dict[str, Any]]  # PageIndex returns array of nodes
    num_pages: Optional[int] = None
    num_nodes: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class Message(BaseModel):
    id: Optional[int] = None
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    tokens: Optional[int] = None
    cost: Optional[float] = None
    created_at: Optional[str] = None


class Conversation(BaseModel):
    id: str
    title: Optional[str] = None
    doc_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConversationCreate(BaseModel):
    title: str
    doc_id: Optional[int] = None
