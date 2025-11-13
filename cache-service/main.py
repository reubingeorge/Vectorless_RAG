from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import json
import hashlib

app = FastAPI(title="Cache Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache (ephemeral - cleared on restart)
cache: Dict[str, Dict[str, Any]] = {}

# Cache statistics
stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "evictions": 0,
    "start_time": datetime.now()
}

class CacheItem(BaseModel):
    key: str
    value: Any
    ttl_seconds: Optional[int] = Field(default=3600, description="Time to live in seconds")

class CacheQuery(BaseModel):
    query: str
    doc_id: Optional[int] = None

def generate_cache_key(query: str, doc_id: Optional[int] = None) -> str:
    """Generate a cache key from query and doc_id"""
    key_str = f"{query}:{doc_id}" if doc_id else query
    return hashlib.md5(key_str.encode()).hexdigest()

def is_expired(item: Dict[str, Any]) -> bool:
    """Check if cache item is expired"""
    if "expires_at" not in item:
        return False
    return datetime.now() > datetime.fromisoformat(item["expires_at"])

def cleanup_expired():
    """Remove expired items from cache"""
    expired_keys = [key for key, item in cache.items() if is_expired(item)]
    for key in expired_keys:
        del cache[key]
        stats["evictions"] += 1
    return len(expired_keys)

@app.get("/")
async def root():
    return {"service": "Cache Service", "status": "running", "cache_size": len(cache)}

@app.get("/health")
async def health():
    cleanup_expired()
    uptime = (datetime.now() - stats["start_time"]).total_seconds()
    hit_rate = stats["hits"] / (stats["hits"] + stats["misses"]) if (stats["hits"] + stats["misses"]) > 0 else 0

    return {
        "status": "healthy",
        "service": "cache-service",
        "port": 8006,
        "version": "1.0.0",
        "cache_size": len(cache),
        "uptime_seconds": uptime,
        "hit_rate": round(hit_rate, 3),
        "total_hits": stats["hits"],
        "total_misses": stats["misses"]
    }

@app.get("/cache/{key}")
async def get_cache_item(key: str):
    """Get item from cache by key"""
    if key in cache:
        item = cache[key]
        if is_expired(item):
            del cache[key]
            stats["evictions"] += 1
            stats["misses"] += 1
            return {"found": False, "reason": "expired"}

        stats["hits"] += 1
        return {
            "found": True,
            "key": key,
            "value": item["value"],
            "created_at": item["created_at"],
            "expires_at": item.get("expires_at")
        }

    stats["misses"] += 1
    return {"found": False}

@app.post("/cache")
async def set_cache_item(item: CacheItem):
    """Set item in cache"""
    expires_at = None
    if item.ttl_seconds:
        expires_at = (datetime.now() + timedelta(seconds=item.ttl_seconds)).isoformat()

    cache[item.key] = {
        "value": item.value,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at
    }

    stats["sets"] += 1

    return {
        "success": True,
        "key": item.key,
        "expires_at": expires_at
    }

@app.delete("/cache/{key}")
async def delete_cache_item(key: str):
    """Delete item from cache"""
    if key in cache:
        del cache[key]
        return {"success": True, "message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Key not found")

@app.post("/cache/query")
async def cache_query(query: CacheQuery, ttl_seconds: int = 3600):
    """Check if query result is cached"""
    key = generate_cache_key(query.query, query.doc_id)

    if key in cache:
        item = cache[key]
        if is_expired(item):
            del cache[key]
            stats["evictions"] += 1
            stats["misses"] += 1
            return {"found": False, "cache_key": key, "reason": "expired"}

        stats["hits"] += 1
        return {
            "found": True,
            "cache_key": key,
            "result": item["value"],
            "created_at": item["created_at"]
        }

    stats["misses"] += 1
    return {"found": False, "cache_key": key}

@app.post("/cache/query/store")
async def store_query_result(query: CacheQuery, result: Any, ttl_seconds: int = 3600):
    """Store query result in cache"""
    key = generate_cache_key(query.query, query.doc_id)

    expires_at = None
    if ttl_seconds:
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()

    cache[key] = {
        "value": result,
        "query": query.query,
        "doc_id": query.doc_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at
    }

    stats["sets"] += 1

    return {
        "success": True,
        "cache_key": key,
        "expires_at": expires_at
    }

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cache (useful for development)"""
    count = len(cache)
    cache.clear()
    stats["evictions"] += count
    return {"success": True, "items_cleared": count}

@app.post("/cache/cleanup")
async def cleanup_cache():
    """Remove expired items"""
    count = cleanup_expired()
    return {"success": True, "items_removed": count}

@app.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    cleanup_expired()
    uptime = (datetime.now() - stats["start_time"]).total_seconds()
    total_requests = stats["hits"] + stats["misses"]
    hit_rate = stats["hits"] / total_requests if total_requests > 0 else 0

    # Calculate memory usage estimate (rough)
    memory_bytes = len(json.dumps(cache).encode())

    return {
        "cache_size": len(cache),
        "total_hits": stats["hits"],
        "total_misses": stats["misses"],
        "total_sets": stats["sets"],
        "total_evictions": stats["evictions"],
        "hit_rate": round(hit_rate, 3),
        "miss_rate": round(1 - hit_rate, 3),
        "uptime_seconds": round(uptime, 2),
        "memory_bytes_estimate": memory_bytes,
        "memory_mb_estimate": round(memory_bytes / (1024 * 1024), 2)
    }

@app.get("/cache/list")
async def list_cache_keys():
    """List all cache keys (for debugging)"""
    cleanup_expired()
    keys = []
    for key, item in cache.items():
        keys.append({
            "key": key,
            "created_at": item["created_at"],
            "expires_at": item.get("expires_at"),
            "size_bytes": len(json.dumps(item["value"]).encode())
        })
    return {"keys": keys, "count": len(keys)}
