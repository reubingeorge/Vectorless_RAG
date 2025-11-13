"""Pydantic models for settings service"""
from pydantic import BaseModel, Field
from typing import Literal

class APIKeyRequest(BaseModel):
    key: str

class TreeSettings(BaseModel):
    toc_check_page_num: int = Field(default=20, ge=5, le=50)
    max_page_num_each_node: int = Field(default=10, ge=1, le=50)
    max_token_num_each_node: int = Field(default=20000, ge=1000, le=50000)
    min_node_pages: int = Field(default=2, ge=1, le=10)
    max_tree_depth: int = Field(default=5, ge=2, le=10)
    max_retry: int = Field(default=3, ge=1, le=10)  # Maximum retry attempts for API calls
    if_add_node_id: bool = True
    if_add_node_summary: bool = False
    if_add_doc_description: bool = False
    if_add_node_text: bool = False
    if_use_toc: bool = True
    if_use_ocr: bool = False

class QuerySettings(BaseModel):
    response_style: Literal["concise", "balanced", "detailed"] = "balanced"
    max_context_nodes: int = Field(default=5, ge=1, le=20)
    citation_style: Literal["inline", "footnote", "none"] = "inline"
    cache_ttl_hours: int = Field(default=24, ge=1, le=168)
    streaming_enabled: bool = True

class ModelConfig(BaseModel):
    model: Literal["gpt-4o", "gpt5", "gpt5-mini", "gpt5-nano"] = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=3000, ge=100, le=16000)  # Increased for complete answers

class UIPreferences(BaseModel):
    theme: Literal["light", "dark", "system"] = "light"
    font_size: Literal["small", "medium", "large"] = "medium"
    code_theme: Literal["github", "monokai", "dracula"] = "github"
    animation_speed: Literal["off", "reduced", "normal"] = "normal"
    sidebar_position: Literal["left", "right"] = "left"
    show_cost_badges: bool = True
    auto_scroll: bool = True
    sound_enabled: bool = False
