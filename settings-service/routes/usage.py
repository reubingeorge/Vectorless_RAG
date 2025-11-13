"""Usage statistics endpoints"""
from fastapi import APIRouter
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/current-month")
async def get_current_month_usage():
    """Get current month's usage statistics"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()

    # Get current month stats
    current_date = datetime.now().strftime("%Y-%m")
    result = cursor.execute('''
        SELECT
            SUM(queries_count),
            SUM(tokens_used),
            SUM(cost),
            SUM(cache_hits)
        FROM usage_stats
        WHERE date LIKE ?
    ''', (f"{current_date}%",)).fetchone()

    conn.close()

    if result and result[0]:
        total_requests = result[0] + (result[3] or 0)
        cache_hit_rate = (result[3] or 0) / total_requests if total_requests > 0 else 0

        return {
            "total_queries": result[0] or 0,
            "total_cost": round(result[2] or 0, 2),
            "tokens_used": result[1] or 0,
            "cache_hits": result[3] or 0,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "saved_by_cache": round((result[2] or 0) * cache_hit_rate, 2)
        }

    return {
        "total_queries": 0,
        "total_cost": 0.0,
        "tokens_used": 0,
        "cache_hits": 0,
        "cache_hit_rate": 0.0,
        "saved_by_cache": 0.0
    }


@router.post("/log")
async def log_usage(queries: int, tokens: int, cost: float, cache_hit: bool = False):
    """Log usage for statistics"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    # Check if today's record exists
    result = cursor.execute(
        "SELECT id FROM usage_stats WHERE date = ?", (today,)
    ).fetchone()

    if result:
        # Update existing record
        cursor.execute('''
            UPDATE usage_stats
            SET queries_count = queries_count + ?,
                tokens_used = tokens_used + ?,
                cost = cost + ?,
                cache_hits = cache_hits + ?
            WHERE date = ?
        ''', (queries, tokens, cost, 1 if cache_hit else 0, today))
    else:
        # Insert new record
        cursor.execute('''
            INSERT INTO usage_stats (date, queries_count, tokens_used, cost, cache_hits)
            VALUES (?, ?, ?, ?, ?)
        ''', (today, queries, tokens, cost, 1 if cache_hit else 0))

    conn.commit()
    conn.close()

    return {"success": True}
