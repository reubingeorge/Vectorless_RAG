from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import os
import logging
from openai import AsyncOpenAI
import tiktoken
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Query Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
STORAGE_SERVICE = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8005")
CACHE_SERVICE = os.getenv("CACHE_SERVICE_URL", "http://cache-service:8006")
SETTINGS_SERVICE = os.getenv("SETTINGS_SERVICE_URL", "http://settings-service:8007")

# Models
class QueryRequest(BaseModel):
    question: str
    document_id: int
    use_cache: bool = True
    include_citations: bool = True

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[Dict[str, Any]] = []
    tokens_used: int
    cost: float
    cached: bool = False
    relevant_nodes: List[str] = []
    thinking: str = ""

# Helper functions from PageIndex approach
def remove_fields(data, fields=['text']):
    """Remove specified fields from nested dict/list structure"""
    if isinstance(data, dict):
        return {k: remove_fields(v, fields)
                for k, v in data.items() if k not in fields}
    elif isinstance(data, list):
        return [remove_fields(item, fields) for item in data]
    return data

def create_node_mapping(tree: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Create a flat mapping of node_id -> node data"""
    node_map = {}

    def traverse(node):
        if isinstance(node, dict):
            # If node has an ID, add to map
            if 'node_id' in node:
                node_map[node['node_id']] = node

            # Recursively traverse children
            if 'children' in node and isinstance(node['children'], list):
                for child in node['children']:
                    traverse(child)

            # Also traverse other nested structures
            for value in node.values():
                if isinstance(value, (dict, list)):
                    traverse(value)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(tree)
    return node_map

def count_tokens(text: str, model: str = "gpt-4o-2024-11-20") -> int:
    """Count tokens in text"""
    try:
        # Use gpt-4o for encoding (tiktoken doesn't have dated versions)
        base_model = "gpt-4o" if "gpt-4o" in model else model
        encoding = tiktoken.encoding_for_model(base_model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed: {e}, using estimate")
        return len(text) // 4

def calculate_cost(tokens: int, model: str) -> float:
    """Calculate cost based on tokens and model (prices per million tokens)"""
    costs = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt5": {"input": 1.25, "output": 10.00},
        "gpt5-mini": {"input": 0.25, "output": 2.00},
        "gpt5-nano": {"input": 0.05, "output": 0.40},
    }

    base_model = model if model in costs else "gpt-4o"

    # Assume roughly 2/3 input, 1/3 output
    input_tokens = tokens * 0.66
    output_tokens = tokens * 0.34

    # Prices are per million tokens
    cost = (input_tokens / 1_000_000 * costs[base_model]["input"] +
            output_tokens / 1_000_000 * costs[base_model]["output"])

    return round(cost, 6)

def generate_cache_key(question: str, document_id: int) -> str:
    """Generate cache key from question and document ID"""
    content = f"{question}:{document_id}"
    return hashlib.md5(content.encode()).hexdigest()

async def call_llm(prompt: str, api_key: str, model: str, temperature: float = 0.3, max_tokens: int = 3000) -> tuple[str, int]:
    """Call OpenAI LLM and return response with token count"""
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens

        return content, tokens
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

async def get_api_key() -> str:
    """Get OpenAI API key from Settings Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{SETTINGS_SERVICE}/get-key")
            if response.status_code == 200:
                data = response.json()
                return data.get("key", "")
            else:
                raise HTTPException(status_code=500, detail="Failed to get API key")
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API key: {str(e)}")

async def get_model_config() -> Dict[str, Any]:
    """Get model configuration from Settings Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{SETTINGS_SERVICE}/settings/model")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "model": "gpt-4o-2024-11-20",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
    except Exception as e:
        logger.warning(f"Failed to get model config: {e}, using defaults")
        return {
            "model": "gpt-4o-2024-11-20",
            "temperature": 0.7,
            "max_tokens": 1000,
        }

async def get_query_settings() -> Dict[str, Any]:
    """Get query settings from Settings Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{SETTINGS_SERVICE}/settings/query")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "max_context_nodes": 5,
                    "citation_style": "inline",
                    "cache_ttl_hours": 24,
                }
    except Exception as e:
        logger.warning(f"Failed to get query settings: {e}, using defaults")
        return {
            "max_context_nodes": 5,
            "citation_style": "inline",
            "cache_ttl_hours": 24,
        }

async def get_tree_from_storage(document_id: int) -> Dict[str, Any]:
    """Get tree structure from Storage Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{STORAGE_SERVICE}/trees/document/{document_id}")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=404, detail="Tree not found for document")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=404, detail="Tree not found for document")
    except Exception as e:
        logger.error(f"Error getting tree: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tree: {str(e)}")

async def check_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Check if query result is cached"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CACHE_SERVICE}/cache", params={"key": cache_key})
            if response.status_code == 200:
                data = response.json()
                if data.get("found"):
                    return data.get("value")
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    return None

async def store_in_cache(cache_key: str, value: Dict[str, Any], ttl: int = 86400):
    """Store query result in cache"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{CACHE_SERVICE}/cache",
                json={"key": cache_key, "value": value, "ttl": ttl}
            )
    except Exception as e:
        logger.warning(f"Cache store failed: {e}")

# PageIndex-style two-stage retrieval
async def stage1_tree_search(
    question: str,
    tree: Dict[str, Any],
    api_key: str,
    model: str
) -> tuple[List[str], str, int]:
    """
    Stage 1: Tree Search (PageIndex approach)
    Pass tree structure (without text) to LLM and ask it to identify relevant node IDs
    Returns: (list of node_ids, thinking_process, tokens_used)
    """
    logger.info(f"Stage 1: Tree search with reasoning")

    # Remove text fields to reduce prompt size (PageIndex approach)
    tree_without_text = remove_fields(tree.copy(), fields=['text'])

    # Create search prompt (following PageIndex pattern)
    search_prompt = f"""You are given a question and a tree structure of a document.
Each node contains a node id, node title, and corresponding page numbers.
Your task is to find all nodes that are likely to contain the answer to the question.

Question: {question}

Document tree structure:
{json.dumps(tree_without_text, indent=2)}

Please reply in the following JSON format:
{{
    "thinking": "<Your thinking process on which nodes are relevant to the question>",
    "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
}}

Directly return the final JSON structure. Do not output anything else."""

    # Call LLM
    result, tokens = await call_llm(search_prompt, api_key, model, temperature=0.3, max_tokens=2000)

    # Parse result
    try:
        # Extract JSON from response (handle code blocks)
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            json_lines = [l for l in lines if l.strip() and not l.strip().startswith("```")]
            result = "\n".join(json_lines)

        result_json = json.loads(result)
        node_list = result_json.get("node_list", [])
        thinking = result_json.get("thinking", "")

        logger.info(f"LLM thinking: {thinking}")
        logger.info(f"Selected {len(node_list)} nodes: {node_list}")

        return node_list, thinking, tokens
    except Exception as e:
        logger.error(f"Failed to parse tree search result: {e}")
        logger.error(f"Raw result: {result}")
        raise HTTPException(status_code=500, detail=f"Failed to parse tree search result: {str(e)}")

async def stage2_answer_generation(
    question: str,
    node_list: List[str],
    tree: Dict[str, Any],
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    citation_style: str
) -> tuple[str, List[Dict[str, Any]], int]:
    """
    Stage 2: Answer Generation (PageIndex approach)
    Retrieve text from selected nodes and generate answer
    Returns: (answer, citations, tokens_used)
    """
    logger.info(f"Stage 2: Answer generation from {len(node_list)} nodes")

    # Create node mapping
    node_map = create_node_mapping(tree)

    # Extract relevant content and build citations
    relevant_content_parts = []
    citations = []

    for node_id in node_list:
        if node_id in node_map:
            node = node_map[node_id]
            title = node.get("title", "Untitled")
            # Tree uses start_index/end_index, not start_page/end_page
            start_page = node.get("start_index") or node.get("start_page", "?")
            end_page = node.get("end_index") or node.get("end_page", "?")
            text = node.get("text", "")

            if text:
                # Keep physical_index tags for page-level citations
                relevant_content_parts.append(f"[Node {node_id}: {title}, pages {start_page}-{end_page}]\n{text}\n")
                citations.append({
                    "node_id": node_id,
                    "section": title,
                    "start_page": start_page,
                    "end_page": end_page
                })
        else:
            logger.warning(f"Node ID {node_id} not found in node map")

    relevant_content = "\n\n".join(relevant_content_parts)

    if not relevant_content:
        logger.warning("No text content found in selected nodes")
        return "I couldn't find relevant content to answer this question.", [], 0

    # Create answer prompt (PageIndex approach)
    if citation_style == "inline":
        citation_instruction = """When referencing information, cite the specific pages where it appears.
- The context contains <physical_index_X> tags marking each page
- Cite as: (pages X-Y) or (page X) based on which physical_index tags contain the information
- Example: "Risk factors include obesity and age over 55 (pages 7-9)"
- Use the most specific page range possible"""
    elif citation_style == "footnote":
        citation_instruction = """When referencing information, add footnote citations with specific page numbers.
- The context contains <physical_index_X> tags marking each page
- Add footnotes like [1], [2] at the end of sentences
- List sources at the end with specific pages based on physical_index tags"""
    else:
        citation_instruction = "Provide a clear answer based on the context."

    answer_prompt = f"""Answer the question based on the context provided below.

Question: {question}

Context:
{relevant_content}

Instructions:
- Answer the question based ONLY on the provided context
- Use markdown formatting for structure:
  * Use numbered lists (1. 2. 3.) or bullet points (-, *) for multiple items
  * Use **bold** for important terms or headings
  * Use proper line breaks between sections
  * Use indentation for sub-items
- Keep your answer well-structured and easy to scan
- {citation_instruction}
- If the context doesn't contain enough information to answer, say so clearly

Example format:
[For lists] The types include:

1. **First Type**: Description here (page X)
   - Sub-point A
   - Sub-point B

2. **Second Type**: Description here (page Y)

[For explanations] [Topic] is [definition]. Key points include:

- **Point 1**: Details (page X)
- **Point 2**: Details (page Y)

Answer:"""

    # Call LLM
    answer, tokens = await call_llm(answer_prompt, api_key, model, temperature=temperature, max_tokens=max_tokens)

    logger.info(f"Generated answer ({tokens} tokens)")
    return answer, citations, tokens

# API Endpoints
@app.get("/")
async def root():
    return {"service": "Query Service", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "query-service",
        "port": 8003,
        "version": "1.0.0"
    }

@app.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    PageIndex-style two-stage retrieval:
    Stage 1: Tree search - LLM identifies relevant node IDs through reasoning
    Stage 2: Answer generation - Extract text from nodes and generate answer
    """
    logger.info(f"Processing query for document {request.document_id}: {request.question}")

    try:
        # Check cache first
        cached_result = None
        if request.use_cache:
            cache_key = generate_cache_key(request.question, request.document_id)
            cached_result = await check_cache(cache_key)
            if cached_result:
                logger.info("Returning cached result")
                return QueryResponse(**cached_result, cached=True)

        # Get configuration
        api_key = await get_api_key()
        model_config = await get_model_config()
        query_settings = await get_query_settings()

        model = model_config.get("model", "gpt-4o-2024-11-20")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 3000)
        citation_style = query_settings.get("citation_style", "inline")

        # Get tree structure
        tree_data = await get_tree_from_storage(request.document_id)
        tree = tree_data.get("tree_data", {})

        if not tree:
            raise HTTPException(status_code=404, detail="No tree structure found for document")

        # Stage 1: Tree search (PageIndex approach)
        node_list, thinking, tokens_stage1 = await stage1_tree_search(
            question=request.question,
            tree=tree,
            api_key=api_key,
            model=model
        )

        # Stage 2: Answer generation (PageIndex approach)
        answer, citations, tokens_stage2 = await stage2_answer_generation(
            question=request.question,
            node_list=node_list,
            tree=tree,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            citation_style=citation_style if request.include_citations else "none"
        )

        # Calculate total tokens and cost
        total_tokens = tokens_stage1 + tokens_stage2
        cost = calculate_cost(total_tokens, model)

        # Prepare response
        result = QueryResponse(
            question=request.question,
            answer=answer,
            citations=citations if request.include_citations else [],
            tokens_used=total_tokens,
            cost=cost,
            cached=False,
            relevant_nodes=node_list,
            thinking=thinking
        )

        # Cache the result
        if request.use_cache:
            cache_ttl = query_settings.get("cache_ttl_hours", 24) * 3600
            await store_in_cache(cache_key, result.model_dump(), ttl=cache_ttl)

        logger.info(f"Query completed: {total_tokens} tokens, ${cost}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
